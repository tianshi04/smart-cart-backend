from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File, Form
from uuid import UUID, uuid4
import mimetypes

from app import crud, schemas
from app.deps import SessionDep
from app.services.r2_service import r2_service

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.get(
    "/",
    response_model=schemas.ProductResponse,
    summary="Search and filter products"
)
async def get_products(
    session: SessionDep,
    query: str | None = Query(None, description="Search query for product name and description."),
    category_id: UUID | None = Query(None, description="Filter by category ID."),
    min_price: float | None = Query(None, description="Minimum price."),
    max_price: float | None = Query(None, description="Maximum price."),
    skip: int = Query(0, ge=0, description="Skip number of products."),
    limit: int = Query(100, ge=1, le=200, description="Limit number of products."),
) -> schemas.ProductResponse:
    """
    Retrieves a list of products with optional filtering, searching, and pagination.
    """
    products_from_db, total_count = crud.get_products(
        session=session,
        query=query,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        skip=skip,
        limit=limit,
    )

    products_out = []
    for product in products_from_db:
        primary_image = next((img for img in product.images if img.is_primary), None)
        if primary_image:
            primary_image.image_url = r2_service.get_public_url(primary_image.image_url)
        products_out.append(
            schemas.ProductOut(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                categories=product.categories,
                primary_image=primary_image,
            )
        )

    return schemas.ProductResponse(total=total_count, products=products_out)

@router.get(
    "/best-sellers",
    response_model=list[schemas.BestSellerProductOut],
    summary="Get list of best-selling products by week"
)
async def get_best_sellers(
    session: SessionDep,
    limit: int = 10,
) -> list[schemas.BestSellerProductOut]:
    """
    Retrieves a list of the top N best-selling products based on quantity sold in the last 7 days.
    """
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be a positive integer."
        )
    
    best_sellers = crud.get_best_selling_products_weekly(session=session, limit=limit)
    return best_sellers


@router.get(
    "/best-sellers-by-category",
    response_model=list[schemas.CategoryWithBestSellersOut],
    summary="Get top 2 best-selling products for each category"
)
async def get_best_sellers_by_category(
    session: SessionDep
) -> list[schemas.CategoryWithBestSellersOut]:
    """
    Retrieves the top 2 best-selling products for each category.
    Requires authentication.
    """
    return crud.get_best_sellers_by_category(session=session)

@router.get(
    "/{product_id}/images",
    response_model=schemas.ProductImageListResponse,
    summary="List all images for a product"
)
async def list_product_images(
    product_id: UUID,
    session: SessionDep,
) -> schemas.ProductImageListResponse:
    """
    Retrieves all images associated with a specific product.
    """
    product = crud.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    images = crud.get_product_images(session=session, product_id=product_id)
    
    # Convert image_url to public URL
    for image in images:
        image.image_url = r2_service.get_public_url(image.image_url)

    return schemas.ProductImageListResponse(images=images)


@router.post(
    "/{product_id}/images",
    response_model=schemas.ProductImageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new image to a product"
)
async def add_product_image(
    product_id: UUID,
    session: SessionDep,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
) -> schemas.ProductImageOut:
    """
    Adds a new image to a specified product by uploading the file.
    If `is_primary` is set to true, any existing primary image for that product will be unset.
    """
    product = crud.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    # Generate a unique filename for R2
    file_extension = mimetypes.guess_extension(file.content_type)
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file type from content."
        )
    unique_filename = f"images/products/{uuid4()}{file_extension}"

    # Read file content
    file_content = await file.read()

    # Upload to R2
    uploaded_file_key = r2_service.upload_file(
        file_content=file_content,
        file_name=unique_filename,
        content_type=file.content_type
    )

    if not uploaded_file_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image to storage."
        )
    
    # Create ProductImageCreate schema with the R2 object key as image_url
    image_create_data = schemas.ProductImageCreate(
        image_url=uploaded_file_key, # Store the R2 object key here
        is_primary=is_primary
    )

    new_image = crud.create_product_image(session=session, product_id=product_id, image_in=image_create_data)
    
    # Return the ProductImageOut with the public URL
    new_image.image_url = r2_service.get_public_url(new_image.image_url)
    return new_image

@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product image"
)
async def delete_product_image(
    image_id: UUID,
    session: SessionDep,
):
    """
    Deletes a specific product image by its ID.
    """
    # Optional: Add role-based access control, e.g., only admins can delete images
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    image = crud.get_product_image_by_id(session, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product image not found."
        )
    
    # Delete from R2 first
    if not r2_service.delete_file(image.image_url):
        # Log error but proceed with DB deletion to avoid orphaned records
        print(f"Warning: Failed to delete image {image.image_url} from R2. Proceeding with DB deletion.")

    crud.delete_product_image(session=session, image=image)
    return {"message": "Product image deleted successfully."}