# Backend for Phong's E-commerce/Retail Application

This repository contains the backend services for an e-commerce or retail application, built with Python and FastAPI. It provides a robust API for managing products, orders, user authentication, and integrates with various services including AI models for product recommendations/search, payment processing, and cloud storage.

## Features

* **User Authentication & Authorization:** Secure user management.
* **Product Management:** CRUD operations for products, categories, and reviews.
* **Order Processing:** Checkout flow, order creation, and management.
* **Shopping Sessions:** Manage user shopping sessions.
* **AI Integration:** AI models for product vectorization and recommendations.
* **Promotions & Favorites:** Functionality for promotions and user favorite products.
* **Notifications:** System for sending notifications.
* **Database Migrations:** Managed with Alembic.
* **Cloud Storage Integration:** R2 service integration.
* **Payment Processing:** Integration with a payment service.

## Technologies Used

* **Python:** Programming language
* **FastAPI:** Web framework for building APIs
* **SQLAlchemy:** ORM for database interactions
* **Alembic:** Database migration tool
* **Uvicorn:** ASGI server for running the FastAPI application
* **uv:** Dependency management (based on `uv.lock`)

## Setup and Installation

Follow these steps to set up the project locally:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/BackendForPhong.git
    cd BackendForPhong
    ```

2. **Install `uv` (if not already installed):**

    ```bash
    pip install uv
    ```

3. **Install dependencies:**

    ```bash
    uv sync
    ```

4. **Environment Variables:**
    Create a `.env` file in the root directory based on `.env.example`.

    ```ini
    # .env.example content (example, adjust as needed)
    DATABASE_URL="postgresql://user:password@host:5432/dbname"
    SECRET_KEY="your_super_secret_key_here"
    ACCESS_TOKEN_EXPIRE_MINUTES=10080 # 7 days

    # PayOS Payment Gateway Integration
    PAYOS_CLIENT_ID="your_payos_client_id"
    PAYOS_API_KEY="your_payos_api_key"
    PAYOS_CHECKSUM_KEY="your_payos_checksum_key"

    # Cloudflare R2 Configuration
    CLOUDFLARE_R2_ACCOUNT_ID=your_r2_account_id
    CLOUDFLARE_R2_ACCESS_KEY_ID=your_r2_access_key_id
    CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
    CLOUDFLARE_R2_BUCKET_NAME=your_r2_bucket_name
    CLOUDFLARE_R2_PUBLIC_URL="https://pub-<YOUR_ACCOUNT_ID>.r2.dev/<YOUR_BUCKET_NAME>"
    ```

    **Note:** For production, use strong, randomly generated keys and secure environment management.

5. **Database Migrations:**
    Apply database migrations using Alembic:

    ```bash
    alembic upgrade head
    ```

## Running the Application

To run the FastAPI application:

```bash
uvicorn app.main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`. You can view the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

## Database Migrations (Alembic)

* **Generate a new migration:**

    ```bash
    alembic revision --autogenerate -m "Description of your migration"
    ```

* **Apply migrations:**

    ```bash
    alembic upgrade head
    ```

* **Revert last migration:**

    ```bash
    alembic downgrade -1
    ```

## API Endpoints (Overview)

The API provides endpoints for:

* `/auth/`: User authentication (login, register, token management)
* `/categories/`: Category management
* `/checkout/`: Checkout process
* `/debug/`: Debugging endpoints (if enabled)
* `/favorites/`: User favorite products
* `/models/`: AI model related operations
* `/notifications/`: User notifications
* `/orders/`: Order management
* `/products/`: Product management
* `/promotions/`: Promotion management
* `/reviews/`: Product reviews
* `/sessions/`: Shopping session management
* `/vectors/`: Product vector related operations

Refer to the interactive API documentation (`/docs`) for detailed endpoint specifications.

## Contributing

Contributions are welcome! Please follow the standard GitHub flow: fork the repository, create a new branch for your features or bug fixes, and submit a pull request.

## License

[Specify your license here, e.g., MIT License]
