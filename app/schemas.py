from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# ----- Auth Schemas ----

class UserCreate(BaseModel):
    """Schema for the request body when registering a new user."""
    full_name: str = Field(..., description="Full name of the user.")
    email: str = Field(..., description="Email address of the user.")
    password: str = Field(..., description="Password of the user.")

class UserOut(BaseModel):
    """Schema for the response when a user is successfully registered."""
    id: UUID
    email: str
    full_name: str
    
    class Config:
        from_attributes = True
    
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Request Schemas (Định nghĩa dữ liệu đầu vào cho các API) ---

class QRAuthTokenUserAuthenticateRequest(BaseModel):
    """
    Schema cho request body khi người dùng xác thực mã QR.
    """
    token: str = Field(..., description="Token của mã QR được quét.")
    user_id: UUID = Field(..., description="ID của người dùng đang thực hiện xác thực.")


# --- Response Schemas (Định nghĩa cấu trúc dữ liệu đầu ra cho các API) ---

class QRGenerateResponse(BaseModel):
    """Schema cho phản hồi khi tạo mã QR mới cho xe đẩy."""
    token: str = Field(..., description="Token duy nhất được tạo cho mã QR.")
    expires_at: datetime = Field(..., description="Thời gian hết hạn của token.")

class QRVerifyRequest(BaseModel):
    token: str = Field(..., description="Token cần verify.")

class QRAuthStatusResponse(BaseModel):
    """Schema cho phản hồi khi kiểm tra trạng thái của mã QR (dùng cho xe đẩy)."""
    status: str = Field(..., description="Trạng thái hiện tại của token QR (pending, authenticated, expired).")
    user: UserOut | None = Field(None, description="Thông tin người dùng nếu token đã được xác thực.")
    session_id: UUID | None = Field(None, description="ID của phiên mua hàng nếu được tạo.")

# --- New Schemas for Favorites ---

class ProductIdRequest(BaseModel):
    """Schema for requests involving a single product ID."""
    product_id: UUID = Field(..., description="ID of the product.")

class FavoriteProductOut(BaseModel):
    """Schema for returning a favorite product's details."""
    id: UUID
    name: str
    price: Decimal
    # Add other relevant product fields if needed
    
    class Config:
        from_attributes = True

class FavoriteStatusResponse(BaseModel):
    """Schema for checking if a product is a favorite."""
    product_id: UUID
    is_favorite: bool


# --- New Schemas for Reviews ---

class ProductReviewCreate(BaseModel):
    """Schema for creating a new product review."""
    product_id: UUID = Field(..., description="ID of the product being reviewed.")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars.")
    comment: str | None = Field(None, description="Optional text comment for the review.")

class ProductReviewOut(BaseModel):
    """Schema for returning a product review."""
    id: UUID
    product_id: UUID
    user_id: UUID
    rating: int
    comment: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductReviewsListResponse(BaseModel):
    """Schema for listing multiple product reviews."""
    reviews: list[ProductReviewOut]

# --- New Schemas for Categories ---

class CategoryCreate(BaseModel):
    """Schema for creating a new category."""
    name: str = Field(..., description="Name of the category.")
    parent_id: UUID | None = Field(None, description="ID of the parent category, if applicable.")

class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""
    name: str | None = Field(None, description="Updated name of the category.")
    parent_id: UUID | None = Field(None, description="Updated ID of the parent category, or null to make it a root category.")

class CategoryOut(BaseModel):
    """Schema for returning a category's details."""
    id: UUID
    name: str
    parent_id: UUID | None
    
    class Config:
        from_attributes = True

class CategoryTreeOut(BaseModel):
    """Schema for returning a category in a hierarchical tree structure."""
    id: UUID
    name: str
    children: list["CategoryTreeOut"] = Field(default_factory=list)

    class Config:
        from_attributes = True

# Forward references for recursive schema
CategoryTreeOut.model_rebuild()


# --- New Schemas for Promotions ---

class PromotionCreate(BaseModel):
    """Schema for creating a new promotion."""
    name: str = Field(..., max_length=255)
    description: str
    discount_type: str = Field(..., max_length=50, description="e.g., 'percentage', 'fixed_amount'")
    discount_value: Decimal = Field(..., decimal_places=2, max_digits=10)
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    product_ids: list[UUID] | None = Field(None, description="List of product IDs to apply the promotion to.")
    category_ids: list[UUID] | None = Field(None, description="List of category IDs to apply the promotion to.")


class PromotionUpdate(BaseModel):
    """Schema for updating an existing promotion."""
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    discount_type: str | None = Field(None, max_length=50)
    discount_value: Decimal | None = Field(None, decimal_places=2, max_digits=10)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None
    product_ids: list[UUID] | None = Field(None, description="List of product IDs to apply the promotion to (replaces existing).")
    category_ids: list[UUID] | None = Field(None, description="List of category IDs to apply the promotion to (replaces existing).")


class PromotionProductOut(BaseModel):
    """Simplified product output for promotion details."""
    id: UUID
    name: str
    class Config:
        from_attributes = True

class PromotionCategoryOut(BaseModel):
    """Simplified category output for promotion details."""
    id: UUID
    name: str
    class Config:
        from_attributes = True

class PromotionOut(BaseModel):
    """Schema for returning a promotion's details."""
    id: UUID
    name: str
    description: str
    discount_type: str
    discount_value: Decimal
    start_date: datetime
    end_date: datetime
    is_active: bool
    applicable_products: list[PromotionProductOut] = Field(default_factory=list)
    applicable_categories: list[PromotionCategoryOut] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

class PromotionLinkProductsRequest(BaseModel):
    product_ids: list[UUID]

class PromotionLinkCategoriesRequest(BaseModel):
    category_ids: list[UUID]
    
# --- New Schemas for Products ---

class ProductImageCreate(BaseModel):
    """Schema for adding a new product image."""
    image_url: str = Field(..., description="URL of the product image.")
    is_primary: bool = Field(False, description="Whether this is the primary image for the product.")

class ProductImageOut(BaseModel):
    """Schema for returning product image details."""
    id: UUID
    product_id: UUID
    image_url: str
    is_primary: bool
    
    class Config:
        from_attributes = True

class ProductImageListResponse(BaseModel):
    """Schema for listing multiple product images."""
    images: list[ProductImageOut]

class BestSellerProductOut(BaseModel):
    """Schema for returning a best-selling product."""
    id: UUID
    name: str
    price: Decimal
    total_quantity_sold: int

    class Config:
        from_attributes = True

class ProductOut(BaseModel):
    """Schema for returning a product with its primary image and category."""
    id: UUID
    name: str
    description: str | None
    price: Decimal
    categories: list[CategoryOut] = []
    primary_image: ProductImageOut | None

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    """Schema for the response of the product list endpoint."""
    total: int
    products: list[ProductOut]

# --- New Schemas for Notifications ---

class NotificationOut(BaseModel):
    """Schema for returning a single notification."""
    id: UUID
    user_id: UUID
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    """Schema for listing multiple notifications."""
    notifications: list[NotificationOut]


# --- New Schemas for Orders ---

class OrderItemProductOut(BaseModel):
    """Simplified product details for an order item."""
    id: UUID
    name: str
    class Config:
        from_attributes = True

class OrderItemOut(BaseModel):
    """Schema for returning an item within an order."""
    id: UUID
    product_id: UUID
    quantity: int
    price_at_purchase: Decimal
    product: OrderItemProductOut # Include product details

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    """Schema for returning a single order with its items."""
    id: UUID
    session_id: UUID
    total_amount: Decimal
    payment_method: str
    status: str
    gateway_txn_id: str | None
    created_at: datetime
    updated_at: datetime | None
    items: list[OrderItemOut] = Field(default_factory=list) # Include nested order items

    class Config:
        from_attributes = True

class OrderHistoryResponse(BaseModel):
    """Schema for listing multiple orders."""
    orders: list[OrderOut]

# --- Schemas for VietQR Checkout Flow ---

class CheckoutFromCartRequest(BaseModel):
    """Schema for the request body when checkout is initiated by the cart."""
    session_id: UUID = Field(..., description="ID of the shopping session to check out.")

class CheckoutRequestResponse(BaseModel):
    """Schema for the response when requesting a checkout."""
    order_id: UUID
    payment_qr_url: str

class CheckoutStatusResponse(BaseModel):
    """Schema for the response when checking the status of an order."""
    order_id: UUID
    status: str

# A simplified, representative schema for a VietQR webhook payload.
# In a real application, this would match the exact specification from the bank/aggregator.
class VietQRWebhookRequest(BaseModel):
    transactionId: str | None = None
    orderId: str | None = None # This will contain our order_id
    amount: int | None = None
    description: str | None = None
    status: str | None = None # e.g., "SUCCESS"
    signature: str | None = None # For verification

# --- New Schemas for AI Models ---

class AIModelCreate(BaseModel):
    """Schema for creating a new AI model entry."""
    name: str = Field(..., description="Name of the AI model.")
    version: str = Field(..., description="Version of the AI model.")

class AIModelOut(BaseModel):
    """Schema for returning AI model details."""
    id: UUID
    name: str
    version: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class AIModelListResponse(BaseModel):
    """Schema for listing multiple AI models."""
    models: list[AIModelOut]

# --- New Schemas for Shopping Session Items ---

class ShoppingSessionItemIn(BaseModel):
    """Schema for inputting a product and quantity for a shopping session."""
    product_id: UUID = Field(..., description="ID of the product.")
    quantity: int = Field(..., ge=0, description="Quantity of the product. Use 0 to remove the item.")

class ShoppingSessionItemsUpdate(BaseModel):
    """Schema for updating multiple items in a shopping session."""
    items: list[ShoppingSessionItemIn] = Field(..., description="List of items to add, update, or remove.")

class ShoppingSessionItemProductOut(BaseModel):
    """Simplified product details for a shopping session item."""
    id: UUID
    name: str
    price: Decimal
    class Config:
        from_attributes = True

class ShoppingSessionItemOut(BaseModel):
    """Schema for returning an item within a shopping session."""
    id: UUID
    product_id: UUID
    quantity: int
    added_at: datetime
    product: ShoppingSessionItemProductOut # Include product details

    class Config:
        from_attributes = True

class ShoppingSessionOut(BaseModel):
    """Schema for returning a shopping session with its items."""
    id: UUID
    user_id: UUID
    status: str
    created_at: datetime
    items: list[ShoppingSessionItemOut] = Field(default_factory=list) # Include nested session items

    class Config:
        from_attributes = True