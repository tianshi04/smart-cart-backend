from typing import List
from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from app import crud, schemas
from app.deps import CurrentUser, SessionDep
from app.models import Product

router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)

@router.get(
    "/list",
    response_model=List[schemas.FavoriteProductOut],
    summary="List all favorite products for the current user"
)
async def list_favorite_products(
    current_user: CurrentUser,
    session: SessionDep
) -> List[schemas.FavoriteProductOut]:
    """
    Retrieve a list of all products favorited by the current user.
    Requires authentication.
    """
    favorite_products = crud.get_favorite_products_for_user(
        session=session,
        user_id=current_user.id
    )
    return favorite_products

@router.post(
    "/add",
    response_model=schemas.FavoriteStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to the current user's favorites"
)
async def add_product_to_favorites(
    product_in: schemas.ProductIdRequest,
    current_user: CurrentUser,
    session: SessionDep
) -> schemas.FavoriteStatusResponse:
    """
    Add a specified product to the current user's list of favorite products.
    Checks if the product exists and if it's already a favorite.
    Requires authentication.
    """
    # Check if product exists
    product = session.get(Product, product_in.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    # Check if already a favorite
    if crud.is_product_favorite(session, current_user.id, product_in.product_id):
        return schemas.FavoriteStatusResponse(
            product_id=product_in.product_id,
            is_favorite=True
        )

    crud.add_product_to_favorites(
        session=session,
        user_id=current_user.id,
        product_id=product_in.product_id
    )
    return schemas.FavoriteStatusResponse(
        product_id=product_in.product_id,
        is_favorite=True
    )

@router.delete(
    "/remove",
    response_model=schemas.FavoriteStatusResponse,
    summary="Remove a product from the current user's favorites"
)
async def remove_product_from_favorites(
    product_in: schemas.ProductIdRequest,
    current_user: CurrentUser,
    session: SessionDep
) -> schemas.FavoriteStatusResponse:
    """
    Remove a specified product from the current user's list of favorite products.
    Raises a 404 if the product is not found in favorites.
    Requires authentication.
    """
    if not crud.is_product_favorite(session, current_user.id, product_in.product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not in favorites."
        )

    crud.remove_product_from_favorites(
        session=session,
        user_id=current_user.id,
        product_id=product_in.product_id
    )
    return schemas.FavoriteStatusResponse(
        product_id=product_in.product_id,
        is_favorite=False
    )

@router.get(
    "/check/{product_id}",
    response_model=schemas.FavoriteStatusResponse,
    summary="Check if a product is in the current user's favorites"
)
async def check_product_favorite_status(
    product_id: UUID,
    current_user: CurrentUser,
    session: SessionDep
) -> schemas.FavoriteStatusResponse:
    """
    Check if a specific product is currently in the authenticated user's favorites.
    Requires authentication.
    """
    is_fav = crud.is_product_favorite(session, current_user.id, product_id)
    return schemas.FavoriteStatusResponse(
        product_id=product_id,
        is_favorite=is_fav
    )