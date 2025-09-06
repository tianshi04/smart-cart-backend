from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File, Form
from uuid import UUID, uuid4
import mimetypes

from app import crud, schemas
from app.deps import SessionDep
from app.services.ai_service import model_manager
from app.services.r2_service import r2_service

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post(
    "/",
    response_model=schemas.ProductOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product"
)
async def create_product(
    product_in: schemas.ProductCreate,
    session: SessionDep,
) -> schemas.ProductOut:
    """
    Creates a new product with basic information and links it to categories.
    """
    db_product = crud.create_product(session=session, product_in=product_in)
    
    # For the response, ensure primary_image is None as no image is uploaded yet
    # and categories are loaded.
    product_out = schemas.ProductOut(
        id=db_product.id,
        name=db_product.name,
        description=db_product.description,
        price=db_product.price,
        weight_grams=db_product.weight_grams,
        created_at=db_product.created_at,
        updated_at=db_product.updated_at,
        categories=db_product.categories, # Categories should be loaded by crud.create_product
        primary_image=None
    )
    return product_out

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
    "/{product_id}",
    response_model=schemas.ProductOut,
    summary="Get product by ID"
)
async def get_product_by_id(
    product_id: UUID,
    session: SessionDep,
) -> schemas.ProductOut:
    """
    Retrieves a single product by its ID, including its images and categories.
    """
    product = crud.get_product_by_id_with_relations(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    # Convert image_url to public URL for primary image
    primary_image = next((img for img in product.images if img.is_primary), None)
    if primary_image:
        primary_image.image_url = r2_service.get_public_url(primary_image.image_url)

    # Ensure categories are loaded for the response model
    # SQLModel should handle this if relations are set up correctly, but explicit loading helps
    # if not product.categories:
    #     product.categories = []

    product_out = schemas.ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        weight_grams=product.weight_grams,
        created_at=product.created_at,
        updated_at=product.updated_at,
        categories=product.categories,
        primary_image=primary_image
    )
    return product_out

@router.patch(
    "/{product_id}",
    response_model=schemas.ProductOut,
    summary="Update product details"
)
async def update_product(
    product_id: UUID,
    product_in: schemas.ProductUpdate,
    session: SessionDep,
) -> schemas.ProductOut:
    """
    Updates an existing product's basic information and category links.
    """
    db_product = crud.get_product_by_id_with_relations(session, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    updated_product = crud.update_product(session=session, db_product=db_product, product_in=product_in)

    # Convert image_url to public URL for primary image in response
    primary_image = next((img for img in updated_product.images if img.is_primary), None)
    if primary_image:
        primary_image.image_url = r2_service.get_public_url(primary_image.image_url)

    product_out = schemas.ProductOut(
        id=updated_product.id,
        name=updated_product.name,
        description=updated_product.description,
        price=updated_product.price,
        weight_grams=updated_product.weight_grams,
        created_at=updated_product.created_at,
        updated_at=updated_product.updated_at,
        categories=updated_product.categories,
        primary_image=primary_image
    )
    return product_out

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product"
)
async def delete_product(
    product_id: UUID,
    session: SessionDep,
):
    """
    Deletes a product and all its associated data (images from R2, reviews, favorites, etc.).
    Does NOT delete OrderItem records for historical purposes.
    """
    product = crud.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    crud.delete_product(session=session, product_id=product_id)
    return

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
                weight_grams=product.weight_grams,
                created_at=product.created_at,
                updated_at=product.updated_at,
                categories=product.categories,
                primary_image=primary_image,
            )
        )

    return schemas.ProductResponse(total=total_count, products=products_out)



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
    summary="Add an image and generate vectors"
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

    file_extension = mimetypes.guess_extension(file.content_type)
    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine file type."
        )
    unique_filename = f"images/products/{uuid4()}{file_extension}"

    file_content = await file.read()

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
    
    # Generate vectors from the image
    vectors, model_id = model_manager.predict(file_content)
    
    if model_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI model is not ready or failed to provide a model ID."
        )

    # Create ProductImage record
    image_create_data = schemas.ProductImageCreate(
        image_url=uploaded_file_key,
        is_primary=is_primary
    )
    new_image = crud.create_product_image(session=session, product_id=product_id, image_in=image_create_data)

    # Save the generated vectors
    for vector in vectors:
        crud.create_product_vector(
            session=session,
            product_id=product_id,
            model_id=model_id,
            embedding=vector
        )
    
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

@router.put(
    "/images/{image_id}/set-primary",
    response_model=schemas.ProductImageOut,
    summary="Set an existing image as primary"
)
async def set_image_as_primary(
    image_id: UUID,
    session: SessionDep,
) -> schemas.ProductImageOut:
    """
    Sets a specific product image as the primary image for its product.
    Any other primary images for the same product will be unset.
    """
    updated_image = crud.set_primary_image(session=session, image_id=image_id)
    if not updated_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product image not found."
        )
    
    updated_image.image_url = r2_service.get_public_url(updated_image.image_url)
    return updated_image