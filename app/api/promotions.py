from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from app import crud, schemas
from app.deps import SessionDep
from app.models import Product, Category

router = APIRouter(
    prefix="/promotions",
    tags=["Promotions"]
)

@router.post(
    "/",
    response_model=schemas.PromotionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new promotion"
)
async def create_new_promotion(
    promotion_in: schemas.PromotionCreate,
    session: SessionDep,
) -> schemas.PromotionOut:
    """
    Creates a new promotion with specified details and optionally links it to products or categories.
    """
    # Optional: Add superuser check here if only superusers can create promotions
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    # Basic validation for start/end dates
    if promotion_in.start_date >= promotion_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date."
        )

    new_promotion = crud.create_promotion(session=session, promotion_in=promotion_in)
    return new_promotion

@router.get(
    "/",
    response_model=List[schemas.PromotionOut],
    summary="List all promotions"
)
async def list_all_promotions(
    session: SessionDep,
    is_active: Optional[bool] = None
) -> List[schemas.PromotionOut]:
    """
    Retrieves a list of all promotions, optionally filtered by their active status.
    """
    promotions = crud.get_all_promotions(session=session, is_active=is_active)
    return promotions

@router.get(
    "/{promotion_id}",
    response_model=schemas.PromotionOut,
    summary="Get promotion by ID"
)
async def get_promotion_details(
    promotion_id: UUID,
    session: SessionDep,
) -> schemas.PromotionOut:
    """
    Retrieves details of a specific promotion by its ID, including linked products and categories.
    """
    promotion = crud.get_promotion_by_id(session=session, promotion_id=promotion_id)
    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion not found."
        )
    return promotion

@router.put(
    "/{promotion_id}",
    response_model=schemas.PromotionOut,
    summary="Update promotion by ID"
)
async def update_promotion_details(
    promotion_id: UUID,
    promotion_in: schemas.PromotionUpdate,
    session: SessionDep,
) -> schemas.PromotionOut:
    """
    Updates an existing promotion's details and can modify its linked products or categories.
    """
    # Optional: Add superuser check here if only superusers can update promotions
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    db_promotion = crud.get_promotion_by_id(session=session, promotion_id=promotion_id)
    if not db_promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion not found."
        )

    # Basic validation for start/end dates if provided
    if promotion_in.start_date and promotion_in.end_date and promotion_in.start_date >= promotion_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date."
        )
    elif promotion_in.start_date and not promotion_in.end_date and promotion_in.start_date >= db_promotion.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New start date must be before current end date."
        )
    elif promotion_in.end_date and not promotion_in.start_date and db_promotion.start_date >= promotion_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current start date must be before new end date."
        )


    updated_promotion = crud.update_promotion(session=session, db_promotion=db_promotion, promotion_in=promotion_in)
    return updated_promotion

@router.delete(
    "/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete promotion by ID"
)
async def delete_existing_promotion(
    promotion_id: UUID,
    session: SessionDep,
):
    """
    Deletes a promotion.
    """
    # Optional: Add superuser check here if only superusers can delete promotions
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not enough privileges")

    promotion = crud.get_promotion_by_id(session=session, promotion_id=promotion_id)
    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promotion not found."
        )
    crud.delete_promotion(session=session, promotion=promotion)
    return {"message": "Promotion deleted successfully."}

# --- Endpoints for linking/unlinking products and categories ---

@router.post(
    "/{promotion_id}/products",
    status_code=status.HTTP_200_OK,
    summary="Link products to a promotion"
)
async def link_products_to_promotion(
    promotion_id: UUID,
    product_link_in: schemas.PromotionLinkProductsRequest,
    session: SessionDep,
):
    """
    Links specified products to an existing promotion.
    """
    promotion = crud.get_promotion_by_id(session, promotion_id)
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found.")

    for product_id in product_link_in.product_ids:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")
        
        # Check if already linked
        if not any(p.id == product_id for p in promotion.applicable_products):
            crud.add_product_to_promotion(session, promotion_id, product_id)
    
    # Refresh promotion to get updated links
    session.refresh(promotion)
    return {"message": "Products linked to promotion successfully."}

@router.delete(
    "/{promotion_id}/products",
    status_code=status.HTTP_200_OK,
    summary="Unlink products from a promotion"
)
async def unlink_products_from_promotion(
    promotion_id: UUID,
    product_link_in: schemas.PromotionLinkProductsRequest,
    session: SessionDep,
):
    """
    Unlinks specified products from an existing promotion.
    """
    promotion = crud.get_promotion_by_id(session, promotion_id)
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found.")

    for product_id in product_link_in.product_ids:
        crud.remove_product_from_promotion(session, promotion_id, product_id)
    
    return {"message": "Products unlinked from promotion successfully."}

@router.post(
    "/{promotion_id}/categories",
    status_code=status.HTTP_200_OK,
    summary="Link categories to a promotion"
)
async def link_categories_to_promotion(
    promotion_id: UUID,
    category_link_in: schemas.PromotionLinkCategoriesRequest,
    session: SessionDep,
):
    """
    Links specified categories to an existing promotion.
    """
    promotion = crud.get_promotion_by_id(session, promotion_id)
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found.")

    for category_id in category_link_in.category_ids:
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID {category_id} not found.")
        
        # Check if already linked
        if not any(c.id == category_id for c in promotion.applicable_categories):
            crud.add_category_to_promotion(session, promotion_id, category_id)
    
    # Refresh promotion to get updated links
    session.refresh(promotion)
    return {"message": "Categories linked to promotion successfully."}

@router.delete(
    "/{promotion_id}/categories",
    status_code=status.HTTP_200_OK,
    summary="Unlink categories from a promotion"
)
async def unlink_categories_from_promotion(
    promotion_id: UUID,
    category_link_in: schemas.PromotionLinkCategoriesRequest,
    session: SessionDep,
):
    """
    Unlinks specified categories from an existing promotion.
    """
    promotion = crud.get_promotion_by_id(session, promotion_id)
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found.")

    for category_id in category_link_in.category_ids:
        crud.remove_category_from_promotion(session, promotion_id, category_id)
    
    return {"message": "Categories unlinked from promotion successfully."}