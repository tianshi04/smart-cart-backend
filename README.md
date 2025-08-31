# Smart Cart Backend API

## Project Overview

This project provides the backend services for a Smart Cart system, designed to manage products, user interactions, shopping sessions, orders, and integrate with payment gateways. It also includes functionalities for managing AI models.

## Features

- **User Authentication:** Secure user registration and authentication.
- **QR Code Based Session Management:** Generate and verify QR codes to link users with shopping sessions on smart carts.
- **Product Catalog:** Manage products with details, images, categories, and reviews.
- **Shopping Sessions:** Real-time management of items within a user's active shopping session (cart).
- **Favorites:** Allow users to mark products as favorites.
- **Promotions:** Create and manage promotions applicable to products and categories.
- **Order Management:** Handle order creation, status tracking, and history.
- **Payment Integration:** Webhook handling for payment gateway (PayOS) to finalize orders.
- **Notifications:** Send notifications to users for events like successful payments.
- **AI Model Management:**
  - Upload AI model files with metadata (name, version).
  - Download stored AI model files.
  - List all available AI models.
  - Delete AI model files and their metadata.

## Technology Stack

- **Backend Framework:** FastAPI (Python)
- **Database:** PostgreSQL (via SQLModel/SQLAlchemy)
- **Database Migrations:** Alembic
- **Payment Gateway:** PayOS
- **Dependency Management:** uv

## Setup and Installation

### Prerequisites

- Python 3.12
- PostgreSQL database
- `uv`

### 1. Clone the repository

```bash
git clone <repository_url>
cd BackendForPhong
```

### 2. Set up the Python environment

```bash
uv venv
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root based on `.env.example`.

```bash
DATABASE_URL="postgresql://user:password@host:port/dbname"
SECRET_KEY="your_super_secret_key"
ACCESS_TOKEN_EXPIRE_MINUTES=10080 # 7 days

PAYOS_CLIENT_ID="your_payos_client_id"
PAYOS_API_KEY="your_payos_api_key"
PAYOS_CHECKSUM_KEY="your_payos_checksum_key"
```

Ensure your `DATABASE_URL` points to your PostgreSQL instance.

### 4. Run Database Migrations

Apply the database schema:

```bash
alembic upgrade head
```

### 5. Create AI Models Storage Directory

The AI models will be stored in the `ai_models` directory at the project root. Create it if it doesn't exist:

```bash
mkdir -p ai_models
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The API documentation (Swagger UI) will be available at `http://127.0.0.1:8000/docs`.

## API Endpoints

Access the interactive API documentation at `/docs` for detailed information on all available endpoints, request/response schemas, and try-it-out functionality.

## Contributing

Contributions are welcome! Please follow the standard GitHub flow: fork the repository, create a feature branch, make your changes, and submit a pull request.

## License

[Specify your license here, e.g., MIT, Apache 2.0]
