from uuid import UUID, uuid4
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app import crud, schemas
from app.core.config import settings
from app.deps import SessionDep
from app.models import AIModelType

router = APIRouter(
    prefix="/models",
    tags=["AI Models"]
)

async def _save_model_file(file: UploadFile) -> str:
    if not settings.MODELS_DIR.exists():
        settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid4()}_{file.filename}"
    file_location = settings.MODELS_DIR / unique_filename
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    return str(file_location)

@router.post("/crop", response_model=schemas.AIModelOut)
async def upload_crop_model(
    session: SessionDep,
    name: str,
    version: str,
    file: UploadFile = File(...)
):
    """
    Uploads a new CROP model file.
    """
    file_location = await _save_model_file(file)
    db_model = crud.create_ai_model_metadata(
        session=session,
        name=name,
        version=version,
        file_path=file_location,
        model_type=AIModelType.CROP
    )
    return db_model

@router.post("/embedding", response_model=schemas.AIModelOut)
async def upload_embedding_model(
    session: SessionDep,
    name: str,
    version: str,
    file: UploadFile = File(...)
):
    """
    Uploads a new EMBEDDING model file.
    """
    file_location = await _save_model_file(file)
    db_model = crud.create_ai_model_metadata(
        session=session,
        name=name,
        version=version,
        file_path=file_location,
        model_type=AIModelType.EMBEDDING
    )
    return db_model

@router.get("/latest/crop", response_model=schemas.AIModelOut)
async def get_latest_crop_model(session: SessionDep):
    """
    Retrieves the latest CROP model.
    """
    model = crud.get_latest_ai_model_by_type(session, AIModelType.CROP)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No CROP model found.")
    return model

@router.get("/latest/embedding", response_model=schemas.AIModelOut)
async def get_latest_embedding_model(session: SessionDep):
    """
    Retrieves the latest EMBEDDING model.
    """
    model = crud.get_latest_ai_model_by_type(session, AIModelType.EMBEDDING)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No EMBEDDING model found.")
    return model

@router.get("/crop", response_model=schemas.AIModelListResponse)
async def list_crop_models(session: SessionDep):
    """
    Lists all available CROP models.
    """
    models = crud.get_ai_models_by_type(session, AIModelType.CROP)
    return schemas.AIModelListResponse(models=models)

@router.get("/embedding", response_model=schemas.AIModelListResponse)
async def list_embedding_models(session: SessionDep):
    """
    Lists all available EMBEDDING models.
    """
    models = crud.get_ai_models_by_type(session, AIModelType.EMBEDDING)
    return schemas.AIModelListResponse(models=models)

@router.get("/{model_id}/download")
async def download_ai_model(
    model_id: UUID,
    session: SessionDep
):
    """
    Downloads an AI model file by its ID.
    """
    db_model = crud.get_ai_model_by_id(session, model_id)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Model not found.")
    
    file_path = Path(db_model.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model file not found on server.")
    
    return FileResponse(path=file_path, filename=file_path.name, media_type="application/octet-stream")

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_model(
    model_id: UUID,
    session: SessionDep
):
    """
    Deletes an AI model file and its metadata by ID.
    """
    db_model = crud.get_ai_model_by_id(session, model_id)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Model not found.")
    
    file_path = Path(db_model.file_path)
    if file_path.is_file():
        try:
            file_path.unlink() # Delete the physical file
        except OSError as e:
            # Log this error but don't prevent metadata deletion
            print(f"Error deleting model file: {e}")

    crud.delete_ai_model(session, db_model)
    return