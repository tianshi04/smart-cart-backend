from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from uuid import UUID, uuid4
import mimetypes

from app import crud, schemas
from app.deps import SessionDep
from app.services.r2_service import r2_service

router = APIRouter(
    prefix="/banners",
    tags=["Banners"]
)

@router.post(
    "/upload",
    response_model=schemas.BannerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new banner"
)
async def upload_banner(
    session: SessionDep,
    title: str = Form(...),
    target_url: str | None = Form(None),
    is_active: bool = Form(True),
    file: UploadFile = File(...),
):
    """
    Uploads a new banner image and creates a banner record.
    """
    file_extension = mimetypes.guess_extension(file.content_type)
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file type."
        )
    
    unique_filename = f"images/banners/{uuid4()}{file_extension}"
    file_content = await file.read()

    uploaded_file_key = r2_service.upload_file(
        file_content=file_content,
        file_name=unique_filename,
        content_type=file.content_type
    )

    if not uploaded_file_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload banner image to storage."
        )

    banner_in = schemas.BannerCreate(title=title, target_url=target_url, is_active=is_active)
    
    db_banner = crud.create_banner(session=session, banner_in=banner_in, image_url=uploaded_file_key)

    db_banner.image_url = r2_service.get_public_url(db_banner.image_url)
    return db_banner

@router.get(
    "/active",
    response_model=schemas.BannerListResponse,
    summary="Get all active banners"
)
async def get_active_banners(session: SessionDep):
    """
    Retrieves a list of all currently active banners.
    """
    banners = crud.get_active_banners(session=session)
    for banner in banners:
        banner.image_url = r2_service.get_public_url(banner.image_url)
    return schemas.BannerListResponse(banners=banners)

@router.get(
    "/",
    response_model=schemas.BannerListResponse,
    summary="Get all banners"
)
async def get_all_banners(session: SessionDep):
    """
    Retrieves a list of all banners (for admin purposes).
    """
    banners = crud.get_all_banners(session=session)
    for banner in banners:
        banner.image_url = r2_service.get_public_url(banner.image_url)
    return schemas.BannerListResponse(banners=banners)

@router.get(
    "/{banner_id}",
    response_model=schemas.BannerOut,
    summary="Get a single banner by ID"
)
async def get_banner_by_id(banner_id: UUID, session: SessionDep):
    """
    Retrieves details for a single banner by its ID.
    """
    banner = crud.get_banner_by_id(session, banner_id)
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found.")
    banner.image_url = r2_service.get_public_url(banner.image_url)
    return banner

@router.patch(
    "/{banner_id}",
    response_model=schemas.BannerOut,
    summary="Update a banner"
)
async def update_banner(
    banner_id: UUID,
    banner_in: schemas.BannerUpdate,
    session: SessionDep,
):
    """
    Updates a banner's details.
    """
    db_banner = crud.get_banner_by_id(session, banner_id)
    if not db_banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found.")
    
    updated_banner = crud.update_banner(session=session, db_banner=db_banner, banner_in=banner_in)
    updated_banner.image_url = r2_service.get_public_url(updated_banner.image_url)
    return updated_banner

@router.delete(
    "/{banner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a banner"
)
async def delete_banner(banner_id: UUID, session: SessionDep):
    """
    Deletes a banner and its image from storage.
    """
    crud.delete_banner(session=session, banner_id=banner_id)
    return
