from uuid import UUID, uuid4
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app import crud, schemas
from app.core.config import settings
from app.deps import SessionDep

router = APIRouter(
    prefix="/models",
    tags=["AI Models"]
)

@router.post("/upload", response_model=schemas.AIModelOut)
async def upload_ai_model(
    session: SessionDep,
    name: str,
    version: str,
    file: UploadFile = File(...)
):
    """
    Uploads a new AI model file and stores its metadata.
    """
    if not settings.MODELS_DIR.exists():
        settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a unique filename to prevent overwriting
    unique_filename = f"{uuid4()}_{file.filename}"
    file_location = settings.MODELS_DIR / unique_filename
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")

    db_model = crud.create_ai_model_metadata(
        session=session,
        name=name,
        version=version,
        file_path=str(file_location)
    )
    return db_model

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

@router.get("/", response_model=schemas.AIModelListResponse)
async def list_ai_models(
    session: SessionDep
):
    """
    Lists all available AI models.
    """
    models = crud.get_all_ai_models(session)
    return schemas.AIModelListResponse(models=models)

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
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not delete file: {e}")
    else:
        print(f"Warning: Model file not found at {file_path}, deleting metadata only.")

    crud.delete_ai_model(session, db_model)
    return # No content response
