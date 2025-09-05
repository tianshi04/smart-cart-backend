import uuid
import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, String, Text, func


# --- Link Models for Many-to-Many Relationships ---

class UserFavoriteLink(SQLModel, table=True):
    __tablename__ = "user_favorites"
    user_id: uuid.UUID = Field(foreign_key="users.id", primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", primary_key=True)


class ProductCategoryLink(SQLModel, table=True):
    __tablename__ = "product_categories"
    product_id: uuid.UUID = Field(foreign_key="products.id", primary_key=True)
    category_id: uuid.UUID = Field(foreign_key="categories.id", primary_key=True)


class PromotionProductLink(SQLModel, table=True):
    __tablename__ = "promotion_products"
    promotion_id: uuid.UUID = Field(foreign_key="promotions.id", primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", primary_key=True)


class PromotionCategoryLink(SQLModel, table=True):
    __tablename__ = "promotion_categories"
    promotion_id: uuid.UUID = Field(foreign_key="promotions.id", primary_key=True)
    category_id: uuid.UUID = Field(foreign_key="categories.id", primary_key=True)


# --- Core Models ---

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str = Field(max_length=255)
    email: str = Field(sa_column=Column("email", String, unique=True, index=True))
    password_hash: str = Field(max_length=255)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    # Relationships
    shopping_sessions: list["ShoppingSession"] = Relationship(back_populates="user")
    reviews: list["ProductReview"] = Relationship(back_populates="user")
    notifications: list["Notification"] = Relationship(back_populates="user")
    qr_auth_tokens: list["QRAuthToken"] = Relationship(back_populates="user")
    favorite_products: list["Product"] = Relationship(
        back_populates="favorited_by", link_model=UserFavoriteLink
    )


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, sa_column=Column(Text))
    price: Decimal = Field(decimal_places=2, max_digits=10)
    weight_grams: int
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    # Relationships
    images: list["ProductImage"] = Relationship(back_populates="product")
    order_items: list["OrderItem"] = Relationship(back_populates="product")
    reviews: list["ProductReview"] = Relationship(back_populates="product")
    session_items: list["ShoppingSessionItem"] = Relationship(back_populates="product")
    favorited_by: list[User] = Relationship(
        back_populates="favorite_products", link_model=UserFavoriteLink
    )
    categories: list["Category"] = Relationship(
        back_populates="products", link_model=ProductCategoryLink
    )
    promotions: list["Promotion"] = Relationship(
        back_populates="applicable_products", link_model=PromotionProductLink
    )


class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="products.id")
    image_url: str = Field(max_length=255)
    is_primary: bool = Field(default=False)

    product: Product = Relationship(back_populates="images")


# --- Product Organization ---

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="categories.id")

    parent: Optional["Category"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: list["Category"] = Relationship(back_populates="parent")
    products: list[Product] = Relationship(
        back_populates="categories", link_model=ProductCategoryLink
    )
    promotions: list["Promotion"] = Relationship(
        back_populates="applicable_categories", link_model=PromotionCategoryLink
    )


# --- User Interaction ---

class ProductReview(SQLModel, table=True):
    __tablename__ = "product_reviews"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="products.id")
    user_id: uuid.UUID = Field(foreign_key="users.id")
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    product: Product = Relationship(back_populates="reviews")
    user: User = Relationship(back_populates="reviews")


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    title: str = Field(max_length=255)
    message: str = Field(sa_column=Column(Text))
    is_read: bool = Field(default=False)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    user: User = Relationship(back_populates="notifications")


# --- Shopping & Checkout ---

class ShoppingSession(SQLModel, table=True):
    __tablename__ = "shopping_sessions"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    status: str = Field(max_length=50, default="active")
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    user: User = Relationship(back_populates="shopping_sessions")
    order: Optional["Order"] = Relationship(back_populates="session")
    items: list["ShoppingSessionItem"] = Relationship(back_populates="session")
    qr_auth_token: Optional["QRAuthToken"] = Relationship(back_populates="shopping_session")


class ShoppingSessionItem(SQLModel, table=True):
    __tablename__ = "shopping_session_items"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="shopping_sessions.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")
    quantity: int
    added_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    session: ShoppingSession = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="session_items")


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="shopping_sessions.id")
    total_amount: Decimal = Field(decimal_places=2, max_digits=12)
    payment_method: str = Field(max_length=50)
    status: str = Field(max_length=50, default="pending")
    gateway_txn_id: str | None = Field(default=None, max_length=255)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    session: ShoppingSession = Relationship(back_populates="order")
    items: list["OrderItem"] = Relationship(back_populates="order")
    lookup_code: Optional["OrderCodeLookup"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id")
    product_id: uuid.UUID = Field(foreign_key="products.id")
    quantity: int
    price_at_purchase: Decimal = Field(decimal_places=2, max_digits=10)

    order: Order = Relationship(back_populates="items")
    product: Product = Relationship(back_populates="order_items")


class OrderCodeLookup(SQLModel, table=True):
    __tablename__ = "order_code_lookup"

    order_code: int = Field(primary_key=True, index=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", index=True)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    order: Order = Relationship(back_populates="lookup_code")


# --- AI Models ---
class AIModelType(str, enum.Enum):
    CROP = "CROP"
    EMBEDDING = "EMBEDDING"

class AIModel(SQLModel, table=True):
    __tablename__ = "ai_models"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    model_type: AIModelType = Field(
        sa_column=Column(String(50), nullable=False, index=True),
        default=AIModelType.CROP
    )
    name: str = Field(max_length=255, index=True)
    version: str = Field(max_length=50)
    file_path: str = Field(max_length=512, unique=True) # Path to the stored model file
    uploaded_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

class ProductVector(SQLModel, table=True):
    __tablename__ = "product_vectors"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="products.id", index=True)
    model_id: uuid.UUID = Field(foreign_key="ai_models.id", index=True)

    embedding: list = Field(sa_column=Column(JSON))

    product: "Product" = Relationship()
    model: "AIModel" = Relationship()

# --- Promotions & Auth ---

class Promotion(SQLModel, table=True):
    __tablename__ = "promotions"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str = Field(sa_column=Column(Text))
    discount_type: str = Field(max_length=50)
    discount_value: Decimal = Field(decimal_places=2, max_digits=10)
    start_date: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end_date: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    is_active: bool = Field(default=True)

    applicable_products: list[Product] = Relationship(
        back_populates="promotions", link_model=PromotionProductLink
    )
    applicable_categories: list["Category"] = Relationship(
        back_populates="promotions", link_model=PromotionCategoryLink
    )


class QRAuthToken(SQLModel, table=True):
    __tablename__ = "qr_auth_tokens"

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    token: str = Field(sa_column=Column(String, unique=True, index=True))
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    shopping_session_id: uuid.UUID | None = Field(default=None, foreign_key="shopping_sessions.id")
    status: str = Field(max_length=50, default="pending")
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=False)))
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    user: Optional[User] = Relationship(back_populates="qr_auth_tokens")
    shopping_session: Optional[ShoppingSession] = Relationship(back_populates="qr_auth_token")
