# Luồng Dữ Liệu Pipeline Phân Tích Ảnh AI

Tài liệu này mô tả luồng dữ liệu khi một ảnh sản phẩm mới được tải lên hệ thống và được xử lý bởi AI Service.

## Bối cảnh và Điểm Kích Hoạt

- **Mục đích:** Tự động trích xuất các đặc trưng AI (vector) từ một ảnh sản phẩm để phục vụ cho việc nhận dạng sau này.
- **Kích hoạt:** Luồng này được bắt đầu khi có một request `POST` được gửi đến API endpoint:
  `POST /products/{product_id}/images`

## Luồng Dữ Liệu Chi Tiết

1. **API Layer (`products.py`):**
    - Endpoint `add_product_image` nhận file ảnh do người dùng tải lên.
    - Dữ liệu (bytes) của ảnh được đọc và giữ lại.

2. **AI Service Call (`ai_service.py`):**
    - Hàm `add_product_image` gọi đến `model_manager.predict()` và truyền vào dữ liệu ảnh.

3. **AI Pipeline Execution:**
    - `AI Service` thực hiện pipeline xử lý ảnh:
        - **Crop Model (YOLOv8):** Phát hiện tất cả các đối tượng trong ảnh.
        - **NMS:** Lọc và chọn ra các bounding box chính xác nhất.
        - **Embedding Model:** Với mỗi đối tượng đã được cắt ra, mô hình tạo ra một **vector đặc trưng**.
    - `AI Service` trả về một **danh sách các vector** cho API Layer.

4. **Lưu Trữ Vào Cơ Sở Dữ Liệu (`crud.py`):**
    - Hàm `add_product_image` nhận lại danh sách vector.
    - Nó lặp qua danh sách này và gọi hàm `crud.create_product_vector` cho từng vector.
    - Mỗi vector được lưu vào bảng `product_vectors` trong CSDL, cùng với ID của sản phẩm và ID của model AI đã tạo ra nó.

## Mục Đích Cuối Cùng

Các vector được lưu trong CSDL sẽ được dùng làm "dấu vân tay" kỹ thuật số. Xe đẩy thông minh sẽ so sánh hình ảnh nó thấy với các vector này để nhận dạng sản phẩm.
