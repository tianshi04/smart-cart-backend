import asyncio
import logging
from typing import List, Any, Tuple
from uuid import UUID
import cv2

import httpx
import numpy as np
import tensorflow as tf
from PIL import Image
from fastapi import HTTPException
from sqlmodel import Session

# Giả lập sự tồn tại của module crud và schemas
from app import crud
# Thêm các import cần thiết cho việc tạo session độc lập
from app.core.database import engine

from app.services.r2_service import r2_service

# --- Các giá trị Placeholder sẽ được thay thế bằng dữ liệu từ DB --- #
EMBEDDING_OUTPUT_DIMS = 6912
# 320x320 -> yolov8-crop

logging.basicConfig(level=logging.INFO)

class ModelManager:
    """
    Quản lý vòng đời và thực thi của các model TFLite.
    Model được tải về từ URL trong database.
    """
    def __init__(self):
        self.crop_model: Any = None
        self.embedding_model: Any = None
        self.embedding_model_id: UUID | None = None # LƯU LẠI ID CỦA MODEL EMBEDDING
        self.is_ready: bool = False
        self._lock = asyncio.Lock() # Lock để xử lý truy cập đa luồng

    async def _load_model_from_url(self, model_url: str) -> Any:
        """Hàm nội bộ để tải một model .tflite từ URL."""
        async with httpx.AsyncClient() as client:
            try:
                logging.info(f"Đang tải model từ: {model_url}")
                response = await client.get(model_url, timeout=300)
                response.raise_for_status()
                model_content = response.content
                interpreter = tf.lite.Interpreter(model_content=model_content)
                interpreter.allocate_tensors()
                logging.info(f"Đã tải và khởi tạo model từ {model_url} thành công.")
                return interpreter
            except httpx.HTTPStatusError as e:
                logging.error(f"Lỗi HTTP khi tải model từ {model_url}: {e}")
                raise
            except Exception as e:
                logging.error(f"Lỗi không xác định khi tải model từ {model_url}: {e}")
                raise

    async def load_models(self, db: Session):
        """Tải các model AI mới nhất từ thông tin trong database."""
        logging.info("Bắt đầu tải các model AI từ database...")
        try:
            latest_crop_model_info = crud.get_latest_model(db, model_type="CROP")
            latest_embedding_model_info = crud.get_latest_model(db, model_type="EMBEDDING")

            if not latest_crop_model_info or not latest_embedding_model_info:
                raise FileNotFoundError("Không tìm thấy thông tin model CROP hoặc EMBEDDING trong database.")

            crop_model_url = r2_service.get_public_url(latest_crop_model_info.file_path)
            embedding_model_url = r2_service.get_public_url(latest_embedding_model_info.file_path)

            self.crop_model = await self._load_model_from_url(crop_model_url)
            self.embedding_model = await self._load_model_from_url(embedding_model_url)
            self.embedding_model_id = latest_embedding_model_info.id # Lưu lại ID
            
            self.is_ready = True
            logging.info("Tải model AI từ database thành công!")

        except Exception as e:
            self.is_ready = False
            logging.error(f"LỖI KHI TẢI MODEL TỪ DATABASE: {e}", exc_info=True)

    async def load_models_background(self):
        """Hàm này được thiết kế để chạy ở chế độ nền (background task)."""
        logging.info("Tác vụ nền: Bắt đầu tải model AI.")
        async with self._lock:
            if self.is_ready:
                logging.info("Tác vụ nền: Models đã sẵn sàng, không cần tải lại.")
                return
            try:
                with Session(engine) as db:
                    await self.load_models(db=db)
            except Exception as e:
                logging.error(f"Tác vụ nền: Tải model thất bại: {e}", exc_info=True)
        logging.info("Tác vụ nền: Kết thúc.")

    async def reload_models(self):
        """Tải lại tất cả các model một cách an toàn, chạy ở chế độ nền."""
        logging.info("Nhận được yêu cầu tải lại model...")
        asyncio.create_task(self.load_models_background())
        logging.info("Đã lên lịch cho việc tải lại model ở chế độ nền.")

    def predict(self, image_data: bytes) -> Tuple[List[List[float]], UUID | None]:
        """
        Hàm đồng bộ thực hiện pipeline AI và trả về (vectors, model_id).
        """
        if not self.is_ready or self.crop_model is None or self.embedding_model is None:
            raise HTTPException(status_code=503, detail="Model AI chưa sẵn sàng hoặc bị lỗi.")

        logging.info("Bắt đầu pipeline dự đoán...")

        try:
            # 1️⃣ Đọc ảnh với OpenCV
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                raise HTTPException(status_code=400, detail="Không đọc được ảnh từ dữ liệu input.")
            h_orig, w_orig, _ = frame.shape
            
            # 2️⃣ Resize input cho YOLO
            input_shape_yolo = self.crop_model.get_input_details()[0]['shape']
            img_resized = cv2.resize(frame, (input_shape_yolo[1], input_shape_yolo[2]))
            img_input = np.expand_dims(img_resized.astype(np.float32)/255.0, axis=0)
            self.crop_model.set_tensor(self.crop_model.get_input_details()[0]['index'], img_input)
            self.crop_model.invoke()
            output_data = self.crop_model.get_tensor(self.crop_model.get_output_details()[0]['index'])[0].T

            # 3️⃣ Chuẩn bị box & score cho NMS
            boxes_for_nms, scores_for_nms = [], []
            CONFIDENCE_THRESHOLD = 0.7
            IOU_THRESHOLD = 0.4

            for row in output_data:
                score = float(row[4])
                if score > CONFIDENCE_THRESHOLD:
                    x_c, y_c, w_box, h_box = row[0:4]
                    x_min = int((x_c - w_box/2) * w_orig)
                    y_min = int((y_c - h_box/2) * h_orig)
                    box_w = int(w_box * w_orig)
                    box_h = int(h_box * h_orig)
                    boxes_for_nms.append([x_min, y_min, box_w, box_h])
                    scores_for_nms.append(score)

            # 4️⃣ NMS với OpenCV
            surviving_indices = cv2.dnn.NMSBoxes(boxes_for_nms, scores_for_nms, CONFIDENCE_THRESHOLD, IOU_THRESHOLD)

            # 5️⃣ Crop & Embedding
            all_vectors = []
            input_shape_emb = self.embedding_model.get_input_details()[0]['shape']

            if surviving_indices is not None and len(surviving_indices) > 0:
                surviving_indices = np.array(surviving_indices).flatten()
                
                for idx in surviving_indices:
                    x_min, y_min, box_w, box_h = boxes_for_nms[idx]
                    x_max, y_max = x_min + box_w, y_min + box_h
                    crop = frame[y_min:y_max, x_min:x_max]
                    if crop.size == 0:
                        continue

                    # Resize + convert BGR->RGB
                    img_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                    img_resized = img_pil.resize((input_shape_emb[1], input_shape_emb[2]))
                    input_data = np.expand_dims(np.array(img_resized), axis=0)
                    input_data = (input_data.astype(np.float32) - 128).astype(np.int8)

                    # Embedding
                    self.embedding_model.set_tensor(self.embedding_model.get_input_details()[0]['index'], input_data)
                    self.embedding_model.invoke()
                    vector = self.embedding_model.get_tensor(self.embedding_model.get_output_details()[0]['index'])
                    all_vectors.append(vector.flatten().tolist())

            return all_vectors, self.embedding_model_id

        except Exception as e:
            logging.error(f"Lỗi trong pipeline dự đoán: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý AI: {e}")



model_manager = ModelManager()