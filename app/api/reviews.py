from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from app import crud, schemas
from app.deps import CurrentUser, SessionDep
from app.models import Product

router = APIRouter(
    prefix="/review",
    tags=["Reviews"]
)

@router.post(
    "/add",
    response_model=schemas.ProductReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new product review"
)
async def add_product_review(
    review_in: schemas.ProductReviewCreate,
    current_user: CurrentUser,
    session: SessionDep
) -> schemas.ProductReviewOut:
    """
    Submit a new review for a product, including a rating (1-5 stars) and an optional comment.
    Checks if the product exists.
    Requires authentication.
    """
    # Check if product exists
    product = session.get(Product, review_in.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
    new_review = crud.create_product_review(
        session=session,
        user_id=current_user.id,
        product_id=review_in.product_id,
        review_data=review_in
    )
    return new_review

@router.get(
    "/list",
    response_model=schemas.ProductReviewsListResponse,
    summary="List product reviews"
)
async def list_product_reviews(
    session: SessionDep,
    current_user: CurrentUser,
    product_id: UUID | None = None,
    user_id: UUID | None = None,
) -> schemas.ProductReviewsListResponse:
    """
    Retrieve a list of product reviews.
    
    - If `product_id` is provided, lists reviews for that specific product.
    - If `user_id` is provided, lists reviews made by that user. **Note**: If `user_id` is specified, it must match the `current_user`'s ID for security reasons.
    - If neither `product_id` nor `user_id` is provided, lists reviews made by the `current_user`.
    
    Requires authentication.
    """
    if product_id and user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot filter by both product_id and user_id simultaneously."
        )
    
    if product_id:
        reviews = crud.get_reviews_for_product(session=session, product_id=product_id)
    elif user_id:
        # For security, ensure user can only request their own reviews by user_id
        if user_id != current_user.id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view reviews for this user, or user_id must match your authenticated ID."
            )
        reviews = crud.get_reviews_by_user(session=session, user_id=user_id)
    else:
        # Default to listing current user's reviews if no specific filters
        reviews = crud.get_reviews_by_user(session=session, user_id=current_user.id)
        
    return schemas.ProductReviewsListResponse(reviews=reviews)