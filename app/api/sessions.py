from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app import crud, schemas
from app.deps import SessionDep, CurrentUser

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)

@router.post("/generate-qr", response_model=schemas.QRGenerateResponse)
async def generate_qr_code(session: SessionDep) -> schemas.QRGenerateResponse:
    """
    Tạo một mã QR mới phục vụ việc xác thực người dùng.
    Mã QR sẽ hiển thị trên màn hình xe đẩy.
    """
    qr_auth_token = crud.create_qr_auth_token(session)

    return schemas.QRGenerateResponse(
        token=qr_auth_token.token,
        expires_at=qr_auth_token.expires_at
    )

@router.post("/verify-qr", response_model=schemas.QRAuthStatusResponse)
async def verify_qr_code(
    session: SessionDep,
    current_user: CurrentUser,
    request: schemas.QRVerifyRequest
) -> schemas.QRAuthStatusResponse:
    """
    Xác thực token QR, liên kết người dùng và tạo phiên mua sắm.
    """
    token = request.token

    qr_auth_token = crud.get_qr_auth_token_by_token(session, token)
    
    if not qr_auth_token:
        raise HTTPException(status_code=404, detail="Mã QR không hợp lệ hoặc không tồn tại.")
    
    current_time = datetime.now(tz=None)
    if qr_auth_token.expires_at < current_time:
        if qr_auth_token.status != "expired":
            crud.update_qr_auth_token(session, qr_auth_token, "expired")
        raise HTTPException(status_code=400, detail="Mã QR đã hết hạn.")
    
    if qr_auth_token.status == "authenticated":
        raise HTTPException(status_code=400, detail="Mã QR đã được sử dụng.")
    
    # --- LOGIC MỚI: TẠO PHIÊN MUA SẮM ---
    # 1. Lấy hoặc tạo một phiên mua hàng đang hoạt động cho người dùng
    shopping_session = crud.get_or_create_active_session(session, user_id=current_user.id)

    # 2. Cập nhật token QR với status, user_id và session_id mới
    crud.update_qr_auth_token(
        session=session, 
        qr_auth_token=qr_auth_token, 
        new_status="authenticated", 
        user_id=current_user.id,
        session_id=shopping_session.id
    )
    # --- KẾT THÚC LOGIC MỚI ---
        
    return schemas.QRAuthStatusResponse(
        status=qr_auth_token.status,
        user=schemas.UserOut(id=current_user.id, email=current_user.email, full_name=current_user.full_name),
        session_id=shopping_session.id
    )
    
@router.get("/check-qr", response_model=schemas.QRAuthStatusResponse)
async def check_qr_status(
    session: SessionDep,
    token: str
) -> schemas.QRAuthStatusResponse:
    """
    Xe đẩy gọi để kiểm tra trạng thái QR token.
    Nếu đã xác thực, trả về cả thông tin user và session_id.
    """
    qr_auth_token = crud.get_qr_auth_token_by_token(session, token)
    if not qr_auth_token:
        raise HTTPException(status_code=404, detail="Mã QR không tồn tại.")

    current_time = datetime.now(tz=None)

    if qr_auth_token.expires_at < current_time and qr_auth_token.status != "expired":
        crud.update_qr_auth_token(session, qr_auth_token, status="expired")

    user_info = None
    # --- LOGIC MỚI: Chỉ đọc thông tin đã được lưu --- 
    if qr_auth_token.status == "authenticated" and qr_auth_token.user_id:
        user = crud.get_user_by_id(session, qr_auth_token.user_id)
        if user:
            user_info = schemas.UserOut(id=user.id, email=user.email, full_name=user.full_name)

    return schemas.QRAuthStatusResponse(
        status=qr_auth_token.status,
        user=user_info,
        session_id=qr_auth_token.shopping_session_id # Trả về session_id đã được lưu
    )
    
@router.put("/{session_id}/items", response_model=schemas.ShoppingSessionOut)
async def update_shopping_session_items(
    session_id: UUID,
    session: SessionDep,
    items_update: schemas.ShoppingSessionItemsUpdate
) -> schemas.ShoppingSessionOut:
    """
    Cập nhật các mặt hàng trong phiên mua sắm của người dùng.
    - Thêm sản phẩm mới vào phiên.
    - Cập nhật số lượng sản phẩm đã có.
    - Xóa sản phẩm khỏi phiên nếu số lượng là 0.
    """
    # Lấy phiên mua sắm hiện tại của người dùng
    shopping_session = crud.get_session_by_id(session, session_id)

    if not shopping_session:
        raise HTTPException(status_code=404, detail="Phiên mua sắm không tìm thấy.")
    
    if shopping_session.status != "active":
        raise HTTPException(status_code=400, detail="Không thể cập nhật phiên mua sắm không hoạt động.")

    for item_in in items_update.items:
        product = crud.get_product_by_id(session, item_in.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Sản phẩm với ID {item_in.product_id} không tìm thấy.")

        existing_item = crud.get_session_item_by_product_and_session(
            session, shopping_session.id, item_in.product_id
        )

        if item_in.quantity == 0:
            if existing_item:
                crud.remove_item_from_session(session, existing_item)
        elif existing_item:
            crud.update_session_item_quantity(session, existing_item, item_in.quantity)
        else:
            crud.add_item_to_session(session, shopping_session.id, item_in.product_id, item_in.quantity)
    
    # Lấy lại phiên mua sắm với các mặt hàng đã được cập nhật để trả về
    updated_session = crud.get_shopping_session_with_items(session, shopping_session.id)
    if not updated_session:
        raise HTTPException(status_code=500, detail="Không thể lấy phiên mua sắm đã cập nhật.")

    return updated_session