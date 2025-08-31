import httpx
import hmac
import hashlib

from app.core.config import settings

PAYOS_API_URL = "https://api-merchant.payos.vn"

async def create_payment_link(order_code: int, amount: int, description: str) -> str:
    """
    Gọi API của PayOS để tạo một link thanh toán mới.

    Args:
        order_code: Mã đơn hàng (dạng số) đã được tạo và lưu trong lookup table.
        amount: Tổng số tiền cần thanh toán.
        description: Mô tả cho đơn hàng.

    Returns:
        URL của trang thanh toán (checkoutUrl).

    Raises:
        Exception: Nếu việc tạo link thanh toán thất bại.
    """
    # Dữ liệu cần gửi đi, cấu trúc này phải khớp với tài liệu của PayOS
    request_data = {
        "orderCode": order_code,
        "amount": amount,
        "description": description,
        "cancelUrl": "https://your-frontend.com/cancel-payment",
        "returnUrl": "https://your-frontend.com/payment-success",
    }

    # Tạo chữ ký (signature) theo thuật toán HMAC-SHA256 mà PayOS yêu cầu
    # Dữ liệu để tạo chữ ký phải được sắp xếp theo alphabet và nối lại
    signature_data_str = f"amount={request_data['amount']}&cancelUrl={request_data['cancelUrl']}&description={request_data['description']}&orderCode={request_data['orderCode']}&returnUrl={request_data['returnUrl']}"
    
    signature = hmac.new(
        settings.PAYOS_CHECKSUM_KEY.encode('utf-8'),
        signature_data_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Các header cần thiết cho request API
    headers = {
        "x-client-id": settings.PAYOS_CLIENT_ID,
        "x-api-key": settings.PAYOS_API_KEY,
    }

    # Dữ liệu cuối cùng để gửi đi (bao gồm cả chữ ký)
    final_payload = {**request_data, "signature": signature}

    async with httpx.AsyncClient() as client:
        try:
            print(f"Sending request to PayOS: {final_payload}")
            response = await client.post(
                f"{PAYOS_API_URL}/v2/payment-requests",
                json=final_payload,
                headers=headers
            )
            
            # Báo lỗi nếu request không thành công (status code không phải 2xx)
            response.raise_for_status()
            
            response_json = response.json()
            payment_data = response_json.get("data")
            
            if not payment_data or not payment_data.get("checkoutUrl"):
                 print(f"PayOS Error Response: {response_json}")
                 raise Exception("Failed to create payment link: Invalid response from PayOS.")

            # Trả về URL trang thanh toán
            return payment_data["checkoutUrl"]

        except httpx.HTTPStatusError as e:
            # Ghi lại lỗi chi tiết từ API để dễ dàng debug
            print(f"API call to PayOS failed with status {e.response.status_code}: {e.response.text}")
            raise Exception(f"Failed to create payment link. Status: {e.response.status_code}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise