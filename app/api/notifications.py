from fastapi import APIRouter
from uuid import UUID

from app import crud, schemas
from app.deps import SessionDep

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get(
    "/{user_id}",
    response_model=schemas.NotificationListResponse,
    summary="Get list of notifications for a user"
)
async def get_user_notifications(
    user_id: UUID,
    session: SessionDep,
) -> schemas.NotificationListResponse:
    """
    Retrieves a list of all notifications for the specified user.
    """
    # if str(user_id) != str(current_user.id):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You are not authorized to view notifications for this user."
    #     )
    
    notifications = crud.get_notifications_for_user(session=session, user_id=user_id)
    return schemas.NotificationListResponse(notifications=notifications)

# Optional: Add an endpoint to mark notifications as read if needed.
# @router.put("/{notification_id}/read", response_model=schemas.NotificationOut)
# async def mark_notification_as_read(...):
#     pass