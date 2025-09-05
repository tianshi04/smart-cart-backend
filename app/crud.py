from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Tuple

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func

# Import tất cả các model bạn đã định nghĩa
from app.models import QRAuthToken
from app import schemas
from app.core import security
from app.models import (
    User, Product, ProductReview, UserFavoriteLink, ProductCategoryLink,
    Category, Promotion, PromotionProductLink, PromotionCategoryLink,
    OrderItem, ProductImage, Order, Notification, ShoppingSession, ShoppingSessionItem,
    OrderCodeLookup, AIModel, AIModelType, ProductVector
)
from app.schemas import (
    ProductReviewCreate,
    CategoryCreate, CategoryUpdate,
    PromotionCreate, PromotionUpdate,
    ProductImageCreate
)
from app.services.r2_service import r2_service # New import


# --- CRUD Operations cho QRAuthToken ---

def create_qr_auth_token(session: Session, expires_in_seconds: int = 120) -> QRAuthToken:
    """
    Tạo một QRAuthToken mới với trạng thái 'pending' và thời gian hết hạn.
    """
    token_uuid = uuid4()
    expires_at = datetime.now(tz=None) + timedelta(seconds=expires_in_seconds)

    qr_auth_token = QRAuthToken(
        token=str(token_uuid),
        status="pending",
        expires_at=expires_at
    )
    session.add(qr_auth_token)
    session.commit()
    session.refresh(qr_auth_token)
    return qr_auth_token

def get_qr_auth_token_by_token(session: Session, token: str) -> QRAuthToken | None:
    """
    Tìm và trả về một QRAuthToken dựa trên giá trị token.
    """
    return session.exec(select(QRAuthToken).where(QRAuthToken.token == token)).first()

def update_qr_auth_token(
    session: Session,
    qr_auth_token: QRAuthToken,
    new_status: str,
    user_id: UUID | None = None,
    session_id: UUID | None = None
) -> QRAuthToken:
    """
    Cập nhật trạng thái, user_id, và session_id cho một QRAuthToken.
    """
    qr_auth_token.status = new_status
    if user_id:
        qr_auth_token.user_id = user_id
    if session_id:
        qr_auth_token.shopping_session_id = session_id
    session.add(qr_auth_token)
    session.commit()
    session.refresh(qr_auth_token)
    return qr_auth_token

# --- CRUD Operations cho User (để kiểm tra sự tồn tại của user_id) ---

def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    """
    Lấy thông tin người dùng dựa trên ID.
    """
    return session.get(User, user_id)

def get_user_by_email(session: Session, email: str) -> User | None:
    """
    Lấy thông tin người dùng dựa trên email.
    """
    return session.exec(select(User).where(User.email == email)).first()

def register_new_user(session: Session, user_data: schemas.UserCreate):
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=security.get_password_hash(user_data.password),
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# --- Favorites CRUD ---
def add_product_to_favorites(session: Session, user_id: UUID, product_id: UUID) -> UserFavoriteLink:
    """Adds a product to a user's favorites."""
    favorite_link = UserFavoriteLink(user_id=user_id, product_id=product_id)
    session.add(favorite_link)
    session.commit()
    session.refresh(favorite_link)
    return favorite_link

def remove_product_from_favorites(session: Session, user_id: UUID, product_id: UUID) -> UserFavoriteLink | None:
    """Removes a product from a user's favorites."""
    statement = select(UserFavoriteLink).where(
        UserFavoriteLink.user_id == user_id,
        UserFavoriteLink.product_id == product_id
    )
    favorite_link = session.exec(statement).first()
    if favorite_link:
        session.delete(favorite_link)
        session.commit()
    return favorite_link

def get_favorite_products_for_user(session: Session, user_id: UUID) -> list[Product]:
    """Retrieves all favorite products for a given user."""
    statement = select(Product).join(UserFavoriteLink).where(UserFavoriteLink.user_id == user_id)
    return session.exec(statement).all()

def is_product_favorite(session: Session, user_id: UUID, product_id: UUID) -> bool:
    """Checks if a product is in a user's favorites."""
    statement = select(UserFavoriteLink).where(
        UserFavoriteLink.user_id == user_id,
        UserFavoriteLink.product_id == product_id
    )
    return session.exec(statement).first() is not None

# --- Reviews CRUD ---
def create_product_review(
    session: Session, user_id: UUID, product_id: UUID, review_data: ProductReviewCreate
) -> ProductReview:
    """Creates a new product review."""
    db_review = ProductReview(
        user_id=user_id,
        product_id=product_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    session.add(db_review)
    session.commit()
    session.refresh(db_review)
    return db_review

def get_reviews_for_product(session: Session, product_id: UUID) -> list[ProductReview]:
    """Retrieves all reviews for a specific product."""
    statement = select(ProductReview).where(ProductReview.product_id == product_id)
    return session.exec(statement).all()

def get_reviews_by_user(session: Session, user_id: UUID) -> list[ProductReview]:
    """Retrieves all reviews made by a specific user."""
    statement = select(ProductReview).where(ProductReview.user_id == user_id)
    return session.exec(statement).all()

# --- Categories CRUD ---

def create_category(session: Session, category_in: CategoryCreate) -> Category:
    """Creates a new category."""
    db_category = Category(**category_in.model_dump())
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

def get_category_by_id(session: Session, category_id: UUID) -> Category | None:
    """Retrieves a category by its ID."""
    return session.get(Category, category_id)

def get_all_categories(session: Session) -> list[Category]:
    """Retrieves all categories."""
    return session.exec(select(Category)).all()

def update_category(session: Session, category: Category, category_in: CategoryUpdate) -> Category:
    """Updates an existing category."""
    for field, value in category_in.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

def delete_category(session: Session, category: Category):
    """Deletes a category."""
    session.delete(category)
    session.commit()

# --- Promotion CRUD ---

def create_promotion(session: Session, promotion_in: PromotionCreate) -> Promotion:
    """Creates a new promotion and links products/categories."""
    promotion_data = promotion_in.model_dump(exclude={"product_ids", "category_ids"})
    db_promotion = Promotion(**promotion_data)

    session.add(db_promotion)
    session.commit()
    session.refresh(db_promotion)

    # Link products
    if promotion_in.product_ids:
        for product_id in promotion_in.product_ids:
            product = session.get(Product, product_id)
            if product:
                db_promotion.applicable_products.append(product)
            else:
                # Handle error or log if product not found
                print(f"Product with ID {product_id} not found for promotion.")

    # Link categories
    if promotion_in.category_ids:
        for category_id in promotion_in.category_ids:
            category = session.get(Category, category_id)
            if category:
                db_promotion.applicable_categories.append(category)
            else:
                # Handle error or log if category not found
                print(f"Category with ID {category_id} not found for promotion.")

    session.add(db_promotion)
    session.commit()
    session.refresh(db_promotion)
    return db_promotion


def get_promotion_by_id(session: Session, promotion_id: UUID) -> Promotion | None:
    """Retrieves a promotion by its ID."""
    statement = select(Promotion).where(Promotion.id == promotion_id)
    return session.exec(statement).first()

def get_all_promotions(session: Session, is_active: bool | None = None) -> list[Promotion]:
    """Retrieves all promotions, optionally filtered by active status."""
    statement = select(Promotion)
    if is_active is not None:
        statement = statement.where(Promotion.is_active == is_active)
    return session.exec(statement).all()

def update_promotion(session: Session, db_promotion: Promotion, promotion_in: PromotionUpdate) -> Promotion:
    """Updates an existing promotion and its linked products/categories."""
    update_data = promotion_in.model_dump(exclude_unset=True, exclude={"product_ids", "category_ids"})
    for field, value in update_data.items():
        setattr(db_promotion, field, value)

    # Handle product links
    if promotion_in.product_ids is not None:
        db_promotion.applicable_products.clear() # Clear existing links
        for product_id in promotion_in.product_ids:
            product = session.get(Product, product_id)
            if product:
                db_promotion.applicable_products.append(product)
            # else: handle error for not found product

    # Handle category links
    if promotion_in.category_ids is not None:
        db_promotion.applicable_categories.clear() # Clear existing links
        for category_id in promotion_in.category_ids:
            category = session.get(Category, category_id)
            if category:
                db_promotion.applicable_categories.append(category)
            # else: handle error for not found category

    session.add(db_promotion)
    session.commit()
    session.refresh(db_promotion)
    return db_promotion

def delete_promotion(session: Session, promotion: Promotion):
    """Deletes a promotion."""
    session.delete(promotion)
    session.commit()

def add_product_to_promotion(session: Session, promotion_id: UUID, product_id: UUID) -> PromotionProductLink | None:
    """Links a product to a promotion."""
    link = PromotionProductLink(promotion_id=promotion_id, product_id=product_id)
    session.add(link)
    session.commit()
    session.refresh(link)
    return link

def remove_product_from_promotion(session: Session, promotion_id: UUID, product_id: UUID) -> bool:
    """Unlinks a product from a promotion."""
    statement = select(PromotionProductLink).where(
        PromotionProductLink.promotion_id == promotion_id,
        PromotionProductLink.product_id == product_id
    )
    link = session.exec(statement).first()
    if link:
        session.delete(link)
        session.commit()
        return True
    return False

def add_category_to_promotion(session: Session, promotion_id: UUID, category_id: UUID) -> PromotionCategoryLink | None:
    """Links a category to a promotion."""
    link = PromotionCategoryLink(promotion_id=promotion_id, category_id=category_id)
    session.add(link)
    session.commit()
    session.refresh(link)
    return link

def remove_category_from_promotion(session: Session, promotion_id: UUID, category_id: UUID) -> bool:
    """Unlinks a category from a promotion."""
    statement = select(PromotionCategoryLink).where(
        PromotionCategoryLink.promotion_id == promotion_id,
        PromotionCategoryLink.category_id == category_id
    )
    link = session.exec(statement).first()
    if link:
        session.delete(link)
        session.commit()
        return True
    return False

# --- Product Related CRUD (New) ---

def get_product_by_id(session: Session, product_id: UUID) -> Product | None:
    """Retrieves a product by its ID."""
    return session.get(Product, product_id)


def get_products(
    session: Session,
    query: str | None = None,
    category_id: UUID | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[list[Product], int]:
    """
    Retrieves a list of products with optional filtering and pagination.
    Returns a tuple containing the list of products and the total count.
    """
    statement = select(Product).options(selectinload(Product.images), selectinload(Product.categories))
    count_statement = select(func.count()).select_from(Product)

    if query:
        search_filter = func.or_(
            Product.name.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%")
        )
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)

    if category_id:
        statement = statement.join(ProductCategoryLink).where(ProductCategoryLink.category_id == category_id)
        count_statement = count_statement.join(ProductCategoryLink).where(ProductCategoryLink.category_id == category_id)

    if min_price is not None:
        statement = statement.where(Product.price >= min_price)
        count_statement = count_statement.where(Product.price >= min_price)

    if max_price is not None:
        statement = statement.where(Product.price <= max_price)
        count_statement = count_statement.where(Product.price <= max_price)

    total_count = session.exec(count_statement).one()

    products = session.exec(statement.offset(skip).limit(limit)).all()
    return products, total_count


def get_best_selling_products_weekly(session: Session, limit: int = 10) -> list[dict]:
    """
    Retrieves a list of best-selling products based on quantity sold in the last 7 days.
    Returns a list of dictionaries with product details and total quantity sold.
    """
    seven_days_ago = datetime.now() - timedelta(days=7)

    statement = (
        select(
            Product.id,
            Product.name,
            Product.price,
            func.sum(OrderItem.quantity).label("total_quantity_sold")
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.created_at >= seven_days_ago)
        .group_by(Product.id, Product.name, Product.price)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    
    results = session.exec(statement).all()
    
    # Convert Row objects to dictionaries for easier Pydantic parsing if needed, or directly use
    # a Pydantic model that can handle these fields.
    best_sellers = []
    for product_id, name, price, total_quantity_sold in results:
        best_sellers.append({
            "id": product_id,
            "name": name,
            "price": price,
            "total_quantity_sold": total_quantity_sold
        })
    return best_sellers

def get_best_sellers_by_category(session: Session) -> list[schemas.CategoryWithBestSellersOut]:
    """
    Retrieves the top 2 best-selling products for each category.
    """
    # Define the subquery for ranking products within each category
    ranked_products_subquery = (
        select(
            Product.id.label("product_id"),
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            Product.name.label("product_name"),
            Product.price.label("product_price"),
            func.sum(OrderItem.quantity).label("total_quantity_sold"),
            func.row_number().over(
                partition_by=Category.id,
                order_by=func.sum(OrderItem.quantity).desc()
            ).label("rn")
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(ProductCategoryLink, Product.id == ProductCategoryLink.product_id)
        .join(Category, ProductCategoryLink.category_id == Category.id)
        .group_by(Category.id, Product.id)
        .cte("ranked_products")
    )

    # Main query to select the top 2 products from the ranked subquery
    statement = (
        select(
            ranked_products_subquery.c.category_id,
            ranked_products_subquery.c.category_name,
            ranked_products_subquery.c.product_id,
            ranked_products_subquery.c.product_name,
            ranked_products_subquery.c.product_price,
            ranked_products_subquery.c.total_quantity_sold
        )
        .where(ranked_products_subquery.c.rn <= 2)
        .order_by(ranked_products_subquery.c.category_name, ranked_products_subquery.c.total_quantity_sold.desc())
    )

    results = session.exec(statement).all()

    # Process the results into the desired output format
    category_map = {}
    for row in results:
        # Get the primary image for the product
        primary_image = session.exec(
            select(ProductImage)
            .where(ProductImage.product_id == row.product_id, ProductImage.is_primary)
        ).first()

        if primary_image:
            primary_image.image_url = r2_service.get_public_url(primary_image.image_url)

        product_out = schemas.BestSellerProductByCategoryOut(
            id=row.product_id,
            name=row.product_name,
            price=row.product_price,
            total_quantity_sold=row.total_quantity_sold,
            primary_image=primary_image
        )

        if row.category_id not in category_map:
            category_map[row.category_id] = schemas.CategoryWithBestSellersOut(
                id=row.category_id,
                name=row.category_name,
                products=[]
            )
        
        category_map[row.category_id].products.append(product_out)

    return list(category_map.values())

# --- Product Image CRUD (New) ---

def create_product_image(session: Session, product_id: UUID, image_in: ProductImageCreate) -> ProductImage:
    """Adds a new image to a product."""
    db_image = ProductImage(product_id=product_id, image_url=image_in.image_url, is_primary=image_in.is_primary)
    
    # Ensure only one primary image per product
    if db_image.is_primary:
        existing_primary = session.exec(
            select(ProductImage).where(
                ProductImage.product_id == product_id,
                ProductImage.is_primary
            )
        ).first()
        if existing_primary:
            existing_primary.is_primary = False
            session.add(existing_primary)

    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    return db_image

def get_product_images(session: Session, product_id: UUID) -> list[ProductImage]:
    """Retrieves all images for a specific product."""
    statement = select(ProductImage).where(ProductImage.product_id == product_id)
    return session.exec(statement).all()

def get_product_image_by_id(session: Session, image_id: UUID) -> ProductImage | None:
    """Retrieves a single product image by its ID."""
    return session.get(ProductImage, image_id)

def delete_product_image(session: Session, image: ProductImage):
    """Deletes a product image."""
    session.delete(image)
    session.commit()

# --- Notifications CRUD (New) ---

def get_notifications_for_user(session: Session, user_id: UUID) -> list[Notification]:
    """Retrieves all notifications for a specific user."""
    statement = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    return session.exec(statement).all()

def create_notification(session: Session, user_id: UUID, title: str, message: str) -> Notification:
    """Creates a new notification for a user."""
    notification = Notification(user_id=user_id, title=title, message=message)
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification

# --- Order History CRUD (New) ---

def get_orders_for_user(session: Session, user_id: UUID) -> list[Order]:
    """
    Retrieves all orders for a specific user, including their order items and related product info.
    """
    # Eagerly load related `ShoppingSession` and `OrderItem` for efficient retrieval
    statement = (
        select(Order)
        .join(ShoppingSession)
        .where(ShoppingSession.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    # Using `.options(selectinload(Order.items).selectinload(OrderItem.product))` would be more
    # explicit for loading relationships, but SQLModel often handles basic relationships well.
    # For nested relationships like Order.items.product, explicit loading is usually better.
    # Here, we'll rely on SQLModel's default or simple relationship access which might lazy load,
    # or rely on the `from_attributes = True` in schemas to guide loading.
    
    orders = session.exec(statement).all()
    return orders

# --- Checkout & Session CRUD ---

def get_session_by_id(session: Session, session_id: UUID) -> ShoppingSession | None:
    """Retrieves a shopping session by its ID."""
    return session.get(ShoppingSession, session_id)

def get_active_session_for_user(session: Session, user_id: UUID) -> ShoppingSession | None:
    """Retrieves the active shopping session for a given user."""
    statement = select(ShoppingSession).where(
        ShoppingSession.user_id == user_id,
        ShoppingSession.status == "active"
    )
    return session.exec(statement).first()

def get_or_create_active_session(session: Session, user_id: UUID) -> ShoppingSession:
    """Retrieves the active shopping session for a user, or creates one if it doesn't exist."""
    active_session = get_active_session_for_user(session, user_id)
    if active_session:
        return active_session
    
    new_session = ShoppingSession(user_id=user_id, status="active")
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    return new_session

def create_order_from_session(session: Session, shopping_session: ShoppingSession) -> Tuple[Order, int]:
    """
    Creates a new Order record from a shopping session with 'pending' status.
    Also creates a lookup entry to map an integer order_code to the UUID order_id.
    Returns the Order object and the generated integer order_code.
    """
    total_amount = 0
    for item in shopping_session.items:
        # In a real scenario, you would also apply promotions here.
        total_amount += item.product.price * item.quantity

    new_order = Order(
        session_id=shopping_session.id,
        total_amount=total_amount,
        payment_method="pending", # Will be updated later
        status="pending",
    )
    session.add(new_order)
    session.commit()
    session.refresh(new_order)

    # Generate a unique integer order_code for the payment gateway
    order_code = new_order.id.int % 2**31

    lookup_entry = OrderCodeLookup(
        order_code=order_code,
        order_id=new_order.id
    )
    session.add(lookup_entry)
    session.commit()

    return new_order, order_code

def get_order_id_by_order_code(session: Session, order_code: int) -> UUID | None:
    """Finds an order_id by the integer order_code from the lookup table."""
    lookup_entry = session.get(OrderCodeLookup, order_code)
    if lookup_entry:
        return lookup_entry.order_id
    return None

def finalize_order_and_session(session: Session, order_id: UUID, gateway_txn_id: str | None) -> Order | None:
    """
    Finalizes a paid order.
    - Updates order status to 'completed'.
    - Copies session items to order items.
    - Updates shopping session status to 'completed'.
    """
    order = session.get(Order, order_id)
    if not order or order.status != "pending":
        return None # Order not found or already processed

    # 1. Update Order
    order.status = "completed"
    order.payment_method = "vietqr_webhook" # Or get from webhook
    order.gateway_txn_id = gateway_txn_id
    
    shopping_session = order.session
    
    # 2. Copy items from ShoppingSessionItem to OrderItem
    if shopping_session:
        for session_item in shopping_session.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=session_item.product_id,
                quantity=session_item.quantity,
                price_at_purchase=session_item.product.price # Price at the moment of checkout
            )
            session.add(order_item)
        
        # 3. Update ShoppingSession
        shopping_session.status = "completed"
        session.add(shopping_session)

    session.add(order)
    session.commit()
    session.refresh(order)
    return order

def get_order_by_id(session: Session, order_id: UUID) -> Order | None:
    """Retrieves an order by its ID."""
    return session.get(Order, order_id)

def get_any_product(session: Session) -> Product | None:
    """Retrieves any single product from the database."""
    return session.exec(select(Product)).first()

# --- AIModel CRUD ---

def create_ai_model_metadata(session: Session, name: str, version: str, file_path: str, model_type: AIModelType) -> AIModel:
    """Creates metadata for a new AI model."""
    db_model = AIModel(name=name, version=version, file_path=file_path, model_type=model_type)
    session.add(db_model)
    session.commit()
    session.refresh(db_model)
    return db_model

def get_ai_model_by_id(session: Session, model_id: UUID) -> AIModel | None:
    """Retrieves an AI model by its ID."""
    return session.get(AIModel, model_id)

def get_ai_models_by_type(session: Session, model_type: AIModelType) -> list[AIModel]:
    """Retrieves all AI models of a specific type."""
    return session.exec(select(AIModel).where(AIModel.model_type == model_type).order_by(AIModel.uploaded_at.desc())).all()

def get_latest_ai_model_by_type(session: Session, model_type: AIModelType) -> AIModel | None:
    """Retrieves the latest AI model of a specific type."""
    statement = (
        select(AIModel)
        .where(AIModel.model_type == model_type)
        .order_by(AIModel.uploaded_at.desc())
    )
    return session.exec(statement).first()

def delete_ai_model(session: Session, db_model: AIModel):
    """Deletes an AI model from the database."""
    session.delete(db_model)
    session.commit()

# --- Product Vector CRUD ---

def create_product_vector(
    session: Session,
    product_id: UUID,
    model_id: UUID,
    embedding: list[float]
) -> ProductVector:
    """
    Creates a new product vector.
    """
    db_vector = ProductVector(
        product_id=product_id,
        model_id=model_id,
        embedding=embedding
    )
    session.add(db_vector)
    session.commit()
    session.refresh(db_vector)
    return db_vector

def get_all_product_vectors(session: Session) -> list[ProductVector]:
    """Retrieves all product vectors from the database."""
    return session.exec(select(ProductVector)).all()

# --- ShoppingSessionItem CRUD ---

def get_session_item_by_product_and_session(
    session: Session, session_id: UUID, product_id: UUID
) -> ShoppingSessionItem | None:
    """Retrieves a shopping session item by session ID and product ID."""
    statement = select(ShoppingSessionItem).where(
        ShoppingSessionItem.session_id == session_id,
        ShoppingSessionItem.product_id == product_id
    )
    return session.exec(statement).first()

def add_item_to_session(
    session: Session, session_id: UUID, product_id: UUID, quantity: int
) -> ShoppingSessionItem:
    """Adds a new item to a shopping session."""
    db_item = ShoppingSessionItem(
        session_id=session_id, product_id=product_id, quantity=quantity
    )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

def update_session_item_quantity(
    session: Session, item: ShoppingSessionItem, new_quantity: int
) -> ShoppingSessionItem:
    """Updates the quantity of an existing shopping session item."""
    item.quantity = new_quantity
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def remove_item_from_session(session: Session, item: ShoppingSessionItem):
    """Removes an item from a shopping session."""
    session.delete(item)
    session.commit()

def get_shopping_session_with_items(session: Session, session_id: UUID) -> ShoppingSession | None:
    """Retrieves a shopping session along with its items and product details."""
    statement = (
        select(ShoppingSession)
        .where(ShoppingSession.id == session_id)
    )
    # Use options to eager load items and their related products
    # This requires `from sqlmodel import select, Relationship` and `from sqlalchemy.orm import selectinload`
    # For simplicity, we'll rely on SQLModel's default loading or access relationships later.
    # If performance is an issue, explicit selectinload would be needed.
    # For now, assuming direct access to `session.items` will trigger lazy loading.
    
    shopping_session = session.exec(statement).first()
    return shopping_session