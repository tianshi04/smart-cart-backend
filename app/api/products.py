from fastapi import APIRouter, HTTPException, status, Query
from uuid import UUID

from app import crud, schemas
from app.deps import SessionDep, CurrentUser

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
    current_user: CurrentUser, # Example: requires authentication
    limit: int = 10,
) -> list[schemas.BestSellerProductOut]:
    """
    Retrieves a list of the top N best-selling products based on quantity sold in the last 7 days.
    Requires authentication.
    """
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be a positive integer."
        )
    
    best_sellers = crud.get_best_selling_products_weekly(session=session, limit=limit)
    return best_sellers

@router.get(
    "/{product_id}/images",
    response_model=schemas.ProductImageListResponse,
    summary="List all images for a product"
)
async def list_product_images(
    product_id: UUID,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication
) -> schemas.ProductImageListResponse:
    """
    Retrieves all images associated with a specific product.
    Requires authentication.
    """
    product = crud.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    images = crud.get_product_images(session=session, product_id=product_id)
    return schemas.ProductImageListResponse(images=images)


@router.post(
    "/{product_id}/images",
    response_model=schemas.ProductImageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new image to a product"
)
async def add_product_image(
    product_id: UUID,
    image_in: schemas.ProductImageCreate,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication (e.g., admin role)
) -> schemas.ProductImageOut:
    """
    Adds a new image URL to a specified product.
    If `is_primary` is set to true, any existing primary image for that product will be unset.
    Requires authentication (e.g., admin privileges).
    """
    # Optional: Add role-based access control, e.g., only admins can add images
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    product = crud.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    new_image = crud.create_product_image(session=session, product_id=product_id, image_in=image_in)
    return new_image

@router.delete(
    "/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product image"
)
async def delete_product_image(
    image_id: UUID,
    session: SessionDep,
    current_user: CurrentUser # Example: requires authentication (e.g., admin role)
):
    """
    Deletes a specific product image by its ID.
    Requires authentication (e.g., admin privileges).
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
    
    crud.delete_product_image(session=session, image=image)
    return {"message": "Product image deleted successfully."}