from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import crud, schemas
from app.deps import get_db

router = APIRouter(
    prefix="/vectors",
    tags=["Vectors"],
)

@router.get("/download", response_model=schemas.ProductVectorListDownloadOut)
def download_all_vectors(*, db: Session = Depends(get_db)):
    """
    Retrieve all product vectors from the database for client-side download.
    """
    all_vectors = crud.get_all_product_vectors(session=db)
    return {"vectors": all_vectors}
