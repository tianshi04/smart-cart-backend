from sqlmodel import Session, select

from app.core import security
from app.models import User, Category, Product, Promotion, ProductCategoryLink

def seed_initial_data(session: Session):
    """
    Seeds the database with initial data for testing if it's empty.
    """
    # 1. Check if data already exists (e.g., by checking for any user)
    statement = select(User)
    first_user = session.exec(statement).first()
    if first_user:
        print("Database already seeded. Skipping.")
        return

    print("Database is empty. Seeding initial data...")

    # 2. Create Categories
    cat_food = Category(name="Thực phẩm")
    cat_drinks = Category(name="Đồ uống")
    cat_household = Category(name="Đồ gia dụng")

    session.add_all([cat_food, cat_drinks, cat_household])
    session.commit()
    session.refresh(cat_food)
    session.refresh(cat_drinks)
    session.refresh(cat_household)

    cat_dairy = Category(name="Sữa & Các sản phẩm từ sữa", parent_id=cat_food.id)
    cat_soda = Category(name="Nước ngọt", parent_id=cat_drinks.id)

    session.add_all([cat_dairy, cat_soda])
    session.commit()
    session.refresh(cat_dairy)
    session.refresh(cat_soda)

    # 3. Create Products
    prod_milk = Product(
        name="Sữa tươi Vinamilk 1L",
        description="Sữa tươi tiệt trùng Vinamilk 100%",
        price=35000,
        weight_grams=1000
    )
    prod_coke = Product(
        name="Coca-Cola Zero Sugar 330ml",
        description="Nước giải khát có ga không đường",
        price=8000,
        weight_grams=330
    )
    prod_detergent = Product(
        name="Nước giặt Omo Matic 4kg",
        description="Nước giặt cho máy giặt cửa trên",
        price=250000,
        weight_grams=4000
    )

    session.add_all([prod_milk, prod_coke, prod_detergent])
    session.commit()
    session.refresh(prod_milk)
    session.refresh(prod_coke)
    session.refresh(prod_detergent)

    # 4. Link Products to Categories
    link_milk_dairy = ProductCategoryLink(product_id=prod_milk.id, category_id=cat_dairy.id)
    link_coke_soda = ProductCategoryLink(product_id=prod_coke.id, category_id=cat_soda.id)
    link_detergent_household = ProductCategoryLink(product_id=prod_detergent.id, category_id=cat_household.id)

    session.add_all([link_milk_dairy, link_coke_soda, link_detergent_household])
    session.commit()

    # 5. Create a test User
    test_user = User(
        full_name="Test User",
        email="test@example.com",
        password_hash=security.get_password_hash("testpassword")
    )
    session.add(test_user)
    session.commit()

    # 6. Create a Promotion
    promo_drinks = Promotion(
        name="Giảm 10% cho tất cả đồ uống",
        description="Áp dụng cho tất cả sản phẩm trong danh mục Đồ uống",
        discount_type="percentage",
        discount_value=10,
        start_date="2025-01-01T00:00:00",
        end_date="2025-12-31T23:59:59",
        is_active=True
    )
    promo_drinks.applicable_categories.append(cat_drinks)
    session.add(promo_drinks)
    session.commit()

    print("Initial data seeded successfully.")
