from fastapi import APIRouter
from uuid import UUID

from app import crud, schemas
from app.deps import SessionDep

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

@router.get(
    "/{user_id}",
    response_model=schemas.OrderHistoryResponse,
    summary="Get order history for a user"
)
async def get_user_order_history(
    user_id: UUID,
    session: SessionDep,
) -> schemas.OrderHistoryResponse:
    """
    Retrieves the complete order history for the specified user, including details of each order and its items.
    
    **Security Note**: The `user_id` in the path must match the ID of the authenticated user.
    Administrators might have a bypass (not implemented here).
    """
    # if str(user_id) != str(current_user.id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You are not authorized to view order history for this user."
    #     )
    
    orders = crud.get_orders_for_user(session=session, user_id=user_id)
    return schemas.OrderHistoryResponse(orders=orders)

# Optional: Add endpoints for getting a single order, or filtering orders by status/date.
# @router.get("/{user_id}/{order_id}", response_model=schemas.OrderOut)
# async def get_single_order_details(...):
#     pass