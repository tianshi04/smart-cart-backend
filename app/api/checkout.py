from fastapi import APIRouter, HTTPException, status, Request
from uuid import UUID
import hmac
import hashlib
import json

from app import crud, schemas
from app.deps import SessionDep
from app.core.config import settings
from app.services import payment_service

router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"]
)

# --- Helper functions from PayOS Documentation ---
# These functions ensure the signature string is created exactly as PayOS expects.

def sort_obj_data_by_key(obj: dict) -> dict:
    return dict(sorted(obj.items()))

def convert_obj_to_query_str(obj: dict) -> str:
    query_string = []
    for key, value in obj.items():
        value_as_string = ""
        if isinstance(value, (int, float, bool)):
            value_as_string = str(value)
        elif value in [None, 'null', 'NULL']:
            value_as_string = ""
        elif isinstance(value, list):
            # Sort objects inside the array before converting to JSON string
            sorted_list = [sort_obj_data_by_key(item) for item in value]
            value_as_string = json.dumps(sorted_list, separators=(',', ':'))
        else:
            value_as_string = str(value)
        query_string.append(f"{key}={value_as_string}")
    return "&".join(query_string)

# --- API Endpoints ---

@router.post("/request", response_model=schemas.CheckoutRequestResponse)
async def request_checkout(
    session: SessionDep,
    request: schemas.CheckoutFromCartRequest # Sử dụng request body mới
):
    """
    Bắt đầu quá trình thanh toán.
    """
    # Tìm phiên mua hàng bằng session_id từ request
    active_session = crud.get_session_by_id(session, request.session_id)
    
    if not active_session or not active_session.items or active_session.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phiên mua hàng không hợp lệ, không có sản phẩm hoặc đã kết thúc."
        )

    # Tạo đơn hàng và mã order_code tương ứng
    pending_order, order_code = crud.create_order_from_session(session, active_session)

    description = "Thanh toan don hang"
    try:
        payment_url = await payment_service.create_payment_link(
            order_code=order_code,
            amount=int(pending_order.total_amount),
            description=description
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể kết nối với cổng thanh toán: {e}"
        )

    return schemas.CheckoutRequestResponse(
        order_id=pending_order.id,
        payment_qr_url=payment_url
    )

@router.get("/status/{order_id}", response_model=schemas.CheckoutStatusResponse)
async def get_checkout_status(
    order_id: UUID,
    session: SessionDep
):
    """
    Kiểm tra định kỳ trạng thái của một đơn hàng đang thanh toán.
    """
    order = crud.get_order_by_id(session, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn hàng.")

    return schemas.CheckoutStatusResponse(
        order_id=order.id,
        status=order.status
    )

@router.post("/webhook/payos")
async def handle_payment_webhook(request: Request, session: SessionDep):
    """
    Xử lý webhook được gửi đến từ PayOS.
    """
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON không hợp lệ")

    # --- Bảo mật: Xác thực chữ ký Webhook từ Body theo tài liệu PayOS ---
    signature_from_payload = payload.get("signature")
    data_object = payload.get("data")

    if not signature_from_payload or not isinstance(data_object, dict):
        raise HTTPException(status_code=400, detail="Webhook không hợp lệ, thiếu signature hoặc data.")

    # Sử dụng các hàm helper từ tài liệu PayOS để tạo chuỗi hash
    sorted_data_by_key = sort_obj_data_by_key(data_object)
    string_to_hash = convert_obj_to_query_str(sorted_data_by_key)

    expected_signature = hmac.new(
        key=settings.PAYOS_CHECKSUM_KEY.encode('utf-8'),
        msg=string_to_hash.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_from_payload):
        print("--- ", "SIGNATURE DEBUG", " ---")
        print(f"STRING TO HASH: \"{string_to_hash}\"")
        print(f"EXPECTED SIG:   \"{expected_signature}\"")
        print(f"RECEIVED SIG:   \"{signature_from_payload}\"")
        raise HTTPException(status_code=403, detail="Chữ ký webhook không hợp lệ.")
    
    print("Signature is valid.")
    # --- Kết thúc phần bảo mật ---

    if payload.get("code") != "00":
        return {"status": "ignored", "reason": "Giao dịch chưa thành công."}

    order_code_from_webhook = data_object.get("orderCode")
    if not order_code_from_webhook:
        raise HTTPException(status_code=400, detail="Webhook không chứa orderCode.")

    order_id = crud.get_order_id_by_order_code(session, order_code=order_code_from_webhook)
    if not order_id:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đơn hàng với mã {order_code_from_webhook}")

    transaction_id = data_object.get("paymentLinkId")

    finalized_order = crud.finalize_order_and_session(
        session=session,
        order_id=order_id,
        gateway_txn_id=transaction_id
    )

    if not finalized_order:
        return {"status": "ignored", "reason": "Đơn hàng không tìm thấy hoặc đã được xử lý."}

    # Create notification for the user
    if finalized_order.session and finalized_order.session.user_id:
        notification_title = "Thanh toán thành công!"
        notification_message = f"Đơn hàng của bạn #{finalized_order.id} đã được thanh toán thành công. Cảm ơn bạn đã mua sắm!"
        crud.create_notification(
            session=session,
            user_id=finalized_order.session.user_id,
            title=notification_title,
            message=notification_message
        )

    print(f"Successfully finalized order {order_id}")
    return {"status": "success"}