from fastapi import APIRouter, HTTPException, status
from app import crud
from app.deps import SessionDep, CurrentUser
from app.models import ShoppingSession, ShoppingSessionItem

router = APIRouter(
    prefix="/debug",
    tags=["Debug"]
)

@router.post("/prepare-cart", summary="Chuẩn bị giỏ hàng để test thanh toán")
async def prepare_cart_for_testing(session: SessionDep, current_user: CurrentUser):
    """
    Tạo một giỏ hàng (phiên mua hàng) và thêm một sản phẩm vào đó.
    Endpoint này chỉ dùng cho mục đích test để nhanh chóng có một giỏ hàng sẵn sàng thanh toán.
    """
    # 1. Lấy một sản phẩm bất kỳ để bỏ vào giỏ
    product_to_add = crud.get_any_product(session)
    if not product_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Không có sản phẩm nào trong database để thêm vào giỏ. Hãy chạy seed data trước."
        )

    # 2. Tìm hoặc tạo một phiên mua hàng đang hoạt động cho người dùng
    active_session = crud.get_active_session_for_user(session, current_user.id)
    if not active_session:
        print(f"No active session for user {current_user.id}, creating one.")
        active_session = ShoppingSession(user_id=current_user.id, status="active")
        session.add(active_session)
        session.commit()
        session.refresh(active_session)
    
    # 3. Xóa các item cũ trong giỏ (nếu có) để đảm bảo giỏ hàng sạch
    for item in active_session.items:
        session.delete(item)
    session.commit()

    # 4. Thêm sản phẩm mới vào giỏ
    cart_item = ShoppingSessionItem(
        session_id=active_session.id, 
        product_id=product_to_add.id, 
        quantity=1
    )
    session.add(cart_item)
    session.commit()
    
    return {
        "message": "Giỏ hàng đã sẵn sàng để checkout.", 
        "session_id": active_session.id, 
        "product_added": {
            "id": product_to_add.id,
            "name": product_to_add.name
        }
    }
