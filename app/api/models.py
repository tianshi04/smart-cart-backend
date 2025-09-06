from uuid import UUID, uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse # New import

from app import crud, schemas
from app.deps import SessionDep
from app.models import AIModelType
from app.services.ai_service import model_manager
from app.services.r2_service import r2_service # New import
import mimetypes # New import

router = APIRouter(
    prefix="/models",
    tags=["AI Models"]
)

@router.post("/crop", response_model=schemas.AIModelOut)
async def upload_crop_model(
    session: SessionDep,
    background_tasks: BackgroundTasks,
    name: str,
    version: str,
    file: UploadFile = File(...)
):
    """
    Uploads a new CROP model file to Cloudflare R2.
    """
    file_content = await file.read()
    file_extension = mimetypes.guess_extension(file.content_type) or ".bin" # Default to .bin if type unknown
    unique_filename = f"models/crop/{name}-{version}-{uuid4()}{file_extension}"

    uploaded_file_key = r2_service.upload_file(
        file_content=file_content,
        file_name=unique_filename,
        content_type=file.content_type
    )

    if not uploaded_file_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload model file to R2."
        )

    db_model = crud.create_ai_model_metadata(
        session=session,
        name=name,
        version=version,
        file_path=uploaded_file_key, # Store the R2 object key
        model_type=AIModelType.CROP
    )
    
    # Schedule model reloading in the background
    background_tasks.add_task(model_manager.reload_models)

    db_model.file_path = r2_service.get_public_url(db_model.file_path) # Return public URL
    return db_model

@router.post("/embedding", response_model=schemas.AIModelOut)
async def upload_embedding_model(
    session: SessionDep,
    background_tasks: BackgroundTasks,
    name: str,
    version: str,
    file: UploadFile = File(...)
):
    """
    Uploads a new EMBEDDING model file to Cloudflare R2.
    """
    file_content = await file.read()
    file_extension = mimetypes.guess_extension(file.content_type) or ".bin" # Default to .bin if type unknown
    unique_filename = f"models/embedding/{name}-{version}-{uuid4()}{file_extension}"

    uploaded_file_key = r2_service.upload_file(
        file_content=file_content,
        file_name=unique_filename,
        content_type=file.content_type
    )

    if not uploaded_file_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload model file to R2."
        )

    db_model = crud.create_ai_model_metadata(
        session=session,
        name=name,
        version=version,
        file_path=uploaded_file_key, # Store the R2 object key
        model_type=AIModelType.EMBEDDING
    )

    # Schedule model reloading in the background
    background_tasks.add_task(model_manager.reload_models)

    db_model.file_path = r2_service.get_public_url(db_model.file_path) # Return public URL
    return db_model

@router.get("/latest/crop", response_model=schemas.AIModelOut)
async def get_latest_crop_model(session: SessionDep):
    """
    Retrieves the latest CROP model.
    """
    model = crud.get_latest_ai_model_by_type(session, AIModelType.CROP)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No CROP model found.")
    model.file_path = r2_service.get_public_url(model.file_path) # Return public URL
    return model

@router.get("/latest/embedding", response_model=schemas.AIModelOut)
async def get_latest_embedding_model(session: SessionDep):
    """
    Retrieves the latest EMBEDDING model.
    """
    model = crud.get_latest_ai_model_by_type(session, AIModelType.EMBEDDING)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No EMBEDDING model found.")
    model.file_path = r2_service.get_public_url(model.file_path) # Return public URL
    return model

@router.get("/crop", response_model=schemas.AIModelListResponse)
async def list_crop_models(session: SessionDep):
    """
    Lists all available CROP models.
    """
    models = crud.get_ai_models_by_type(session, AIModelType.CROP)
    for model in models:
        model.file_path = r2_service.get_public_url(model.file_path) # Return public URL
    return schemas.AIModelListResponse(models=models)

@router.get("/embedding", response_model=schemas.AIModelListResponse)
async def list_embedding_models(session: SessionDep):
    """
    Lists all available EMBEDDING models.
    """
    models = crud.get_ai_models_by_type(session, AIModelType.EMBEDDING)
    for model in models:
        model.file_path = r2_service.get_public_url(model.file_path) # Return public URL
    return schemas.AIModelListResponse(models=models)

@router.get("/{model_id}/download")
async def download_ai_model(
    model_id: UUID,
    session: SessionDep
):
    """
    Downloads an AI model file by its ID from Cloudflare R2.
    """
    db_model = crud.get_ai_model_by_id(session, model_id)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Model not found.")
    
    # Redirect to the R2 public URL
    r2_public_url = r2_service.get_public_url(db_model.file_path)
    return RedirectResponse(url=r2_public_url)

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_model(
    model_id: UUID,
    session: SessionDep
):
    """
    Deletes an AI model file from Cloudflare R2 and its metadata by ID.
    """
    db_model = crud.get_ai_model_by_id(session, model_id)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Model not found.")
    
    # Delete from R2 first
    if not r2_service.delete_file(db_model.file_path):
        # Log error but proceed with DB deletion to avoid orphaned records
        print(f"Warning: Failed to delete model file {db_model.file_path} from R2. Proceeding with DB deletion.")

    crud.delete_ai_model(session, db_model)
    return