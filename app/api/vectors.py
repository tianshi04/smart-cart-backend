from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import io
import json
from sqlmodel import Session

from app import crud, schemas
from app.deps import get_db

router = APIRouter(
    prefix="/vectors",
    tags=["Vectors"],
)

@router.get("/download")
def download_all_vectors(*, db: Session = Depends(get_db)):
    """
    Trả về tất cả product vectors dưới dạng file JSON để tải về.

    File JSON có cấu trúc:

    {
      "vectors": [
        {
          "product_id": "212e0ffb-7b33-40cc-8fe4-024f9fa7b23e",
          "embedding": [0.1, 0.2, 0.3, ...]
        },
        {
          "product_id": "a12f3bcd-4e56-7890-abcd-1234567890ef",
          "embedding": [0.4, 0.5, 0.6, ...]
        }
      ]
    }

    Mỗi mục trong `vectors` chứa:
    - `product_id`: UUID4 của sản phẩm (chuỗi)
    - `embedding`: mảng số biểu diễn vector của sản phẩm
    """
    all_vectors_from_db = crud.get_all_product_vectors(session=db)
    
    simplified_vectors = [
        {"product_id": vec.product_id, "embedding": vec.embedding}
        for vec in all_vectors_from_db
    ]
    
    json_payload = {"vectors": simplified_vectors}
    json_content = json.dumps(json_payload, indent=2, default=str)
    
    string_io = io.StringIO(json_content)
    
    headers = {
        'Content-Disposition': 'attachment; filename="product_vectors.json"'
    }
    
    return StreamingResponse(
        content=iter(string_io.readline, ''),
        media_type="application/json",
        headers=headers
    )


@router.get("/last-updated", response_model=schemas.LastUpdatedOut)
def get_last_updated(*, db: Session = Depends(get_db)):
    """
    Get the timestamp of the most recently added product vector.
    """
    latest_timestamp = crud.get_latest_vector_timestamp(session=db)
    return {"last_updated": latest_timestamp}
