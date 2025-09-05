# API Specification (Updated)

## 1. Thông tin chung

- **Authentication:** Hầu hết các endpoint yêu cầu xác thực đều sử dụng **Bearer Token (JWT)** được gửi qua `Authorization` header. Người dùng lấy token này từ API `POST /auth/login`.
- **Định dạng dữ liệu:** JSON

---

## 2. Authentication API (`/auth`)

Cung cấp chức năng đăng ký và đăng nhập cho người dùng.

### `POST /auth/register`

- **Mô tả:** Đăng ký một tài khoản người dùng mới.
- **Request Body:**

  ```json
  {
    "full_name": "string",
    "email": "user@example.com",
    "password": "string"
  }
  ```

- **Success Response (201 Created):**

  ```json
  {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "string"
  }
  ```

### `POST /auth/login`

- **Mô tả:** Đăng nhập và trả về JWT access token.
- **Request Body:** Dữ liệu form `x-www-form-urlencoded` với `username` (là email) và `password`.
- **Success Response (200 OK):**

  ```json
  {
    "access_token": "your_jwt_token",
    "token_type": "bearer"
  }
  ```

---

## 3. QR Code Login API (`/sessions`)

Cung cấp luồng đăng nhập nhanh cho một thiết bị (ví dụ: xe đẩy) mà không cần nhập mật khẩu.

### `POST /sessions/generate-qr`

- **Mô tả:** Tạo ra một token tạm thời để hiển thị dưới dạng QR code trên thiết bị.
- **Success Response (200 OK):**

  ```json
  {
    "token": "qr-token-uuid",
    "expires_at": "2025-08-30T10:00:00Z"
  }
  ```

### `POST /sessions/verify-qr`

- **Mô tả:** Người dùng (đã đăng nhập trên app điện thoại) quét mã QR và gửi token lên để xác thực cho thiết bị.
- **Yêu cầu:** Xác thực JWT của người dùng.
- **Request Body:**

  ```json
  {
    "token": "qr-token-uuid"
  }
  ```

- **Success Response (200 OK):**

  ```json
  {
    "status": "authenticated",
    "user": { ... },
    "session_id": "shopping-session-uuid"
  }
  ```

### `GET /sessions/check-qr`

- **Mô tả:** Thiết bị (xe đẩy) gọi API này lặp lại để kiểm tra xem mã QR đã được người dùng xác thực hay chưa.
- **Query Params:** `token` (string, required).
- **Success Response (200 OK):**

  ```json
  {
    "status": "pending | authenticated | expired",
    "user": { ... } // (null nếu chưa authenticated)
  }
  ```

### `PUT /sessions/{session_id}/items`

- **Mô tả:** Cập nhật các mặt hàng trong phiên mua sắm của người dùng. Có thể thêm sản phẩm mới, cập nhật số lượng sản phẩm đã có, hoặc xóa sản phẩm (nếu số lượng là 0).
- **URL Params:** `session_id` (UUID, required).
- **Request Body:**

  ```json
  {
    "items": [
      {
        "product_id": "product-uuid",
        "quantity": 1
      }
    ]
  }
  ```

- **Success Response (200 OK):** Trả về thông tin phiên mua sắm đã cập nhật, bao gồm danh sách các mặt hàng.

  ```json
  {
    "id": "session-uuid",
    "user_id": "user-uuid",
    "status": "active",
    "created_at": "2025-08-30T10:00:00Z",
    "items": [
      {
        "id": "item-uuid",
        "product_id": "product-uuid",
        "quantity": 1,
        "added_at": "2025-08-30T10:00:00Z",
        "product": {
          "id": "product-uuid",
          "name": "Tên sản phẩm",
          "price": 100.00
        }
      }
    ]
  }
  ```

---

## 4. Checkout & Payment API (`/checkout`)

Cung cấp luồng thanh toán tích hợp với cổng thanh toán (PayOS).

### `POST /checkout/request`

- **Mô tả:** Bắt đầu quá trình thanh toán cho giỏ hàng hiện tại của người dùng.
- **Yêu cầu:** Xác thực JWT của người dùng.
- **Request Body:**

  ```json
  {
    "session_id": "shopping-session-uuid"
  }
  ```

- **Success Response (200 OK):** Trả về ID đơn hàng và URL thanh toán để hiển thị QR.

  ```json
  {
    "order_id": "order-uuid",
    "payment_qr_url": "https://link-or-qr-image-url.com/pay?order_id=..."
  }
  ```

### `GET /checkout/status/{order_id}`

- **Mô tả:** Client gọi để kiểm tra trạng thái của đơn hàng sau khi người dùng quét mã QR.
- **URL Params:** `order_id` (UUID, required).
- **Success Response (200 OK):**

  ```json
  {
    "order_id": "order-uuid",
    "status": "pending | completed | failed"
  }
  ```

### `POST /checkout/webhook/payos`

- **Mô tả:** Endpoint để nhận thông báo (webhook) từ PayOS khi giao dịch thanh toán có cập nhật.
- **Actor:** PayOS Server.
- **Request Body:** Cấu trúc theo quy định của PayOS.
- **Success Response (200 OK):** `{ "status": "success" }`

---

## 5. Resource Management APIs

Các API sau đây là các endpoint RESTful tiêu chuẩn để quản lý các tài nguyên khác nhau của hệ thống. Hầu hết đều yêu cầu xác thực JWT của người dùng.

- **`/products`**: Tìm kiếm, lọc, lấy danh sách sản phẩm bán chạy, quản lý hình ảnh sản phẩm.
- **`/categories`**: Quản lý danh mục (CRUD), lấy cấu trúc cây danh mục.
- **`/reviews`**: Thêm và xem đánh giá sản phẩm.
- **`/favorites`**: Quản lý danh sách sản phẩm yêu thích của người dùng.
- **`/promotions`**: Quản lý các chương trình khuyến mãi.
- **`/orders`**: Xem lịch sử đơn hàng của người dùng đã đăng nhập.
- **`/notifications`**: Xem danh sách thông báo của người dùng.

---

## 6. Product API (`/products`)

### `GET /products/`

- **Mô tả:** Tìm kiếm và lọc sản phẩm.
- **Query Params:**
  - `query` (string, optional): Chuỗi tìm kiếm theo tên và mô tả sản phẩm.
  - `category_id` (UUID, optional): Lọc sản phẩm theo ID danh mục.
  - `min_price` (float, optional): Giá tối thiểu.
  - `max_price` (float, optional): Giá tối đa.
  - `skip` (int, optional, default: 0): Bỏ qua bao nhiêu sản phẩm đầu tiên (để phân trang).
  - `limit` (int, optional, default: 100): Giới hạn số lượng sản phẩm trả về.
- **Success Response (200 OK):**

  ```json
  {
    "total": 120,
    "products": [
      {
        "id": "product-uuid",
        "name": "Tên sản phẩm",
        "description": "Mô tả sản phẩm",
        "price": 50.00,
        "categories": [
          {
            "id": "category-uuid",
            "name": "Tên danh mục",
            "parent_id": null
          }
        ],
        "primary_image": {
          "id": "image-uuid",
          "product_id": "product-uuid",
          "image_url": "http://example.com/image.png",
          "is_primary": true
        }
      }
    ]
  }
  ```

### `GET /products/best-sellers`

- **Mô tả:** Lấy danh sách các sản phẩm bán chạy nhất theo tuần.
- **Query Params:**
  - `limit` (int, optional, default: 10): Giới hạn số lượng sản phẩm trả về.
- **Success Response (200 OK):**

  ```json
  [
    {
      "id": "product-uuid",
      "name": "Tên sản phẩm",
      "price": 10.00,
      "total_quantity_sold": 150
    }
  ]
  ```

### `GET /products/best-sellers-by-category`

- **Mô tả:** Lấy danh sách 2 sản phẩm bán chạy nhất cho mỗi danh mục.
- **Yêu cầu:** Xác thực JWT của người dùng.
- **Success Response (200 OK):**

  ```json
  [
    {
      "id": "category-uuid-1",
      "name": "Đồ uống",
      "products": [
        {
          "id": "product-uuid-a",
          "name": "Coca-Cola",
          "price": 10.00,
          "total_quantity_sold": 150,
          "primary_image": { ... }
        },
        {
          "id": "product-uuid-b",
          "name": "Pepsi",
          "price": 10.00,
          "total_quantity_sold": 120,
          "primary_image": { ... }
        }
      ]
    },
    {
      "id": "category-uuid-2",
      "name": "Đồ ăn vặt",
      "products": [
        {
          "id": "product-uuid-c",
          "name": "Oishi Snack",
          "price": 5.00,
          "total_quantity_sold": 200,
          "primary_image": { ... }
        },
        {
          "id": "product-uuid-d",
          "name": "Lay's Stax",
          "price": 20.00,
          "total_quantity_sold": 180,
          "primary_image": { ... }
        }
      ]
    }
  ]
  ```

---

## 7. AI Model Management API (`/models`)

Cung cấp các chức năng để tải lên, tải xuống, liệt kê và xóa các mô hình AI.

### `POST /models/crop`

- **Mô tả:** Tải lên một tệp mô hình AI mới thuộc loại CROP và lưu trữ metadata của nó.
- **Request Body:** `multipart/form-data`
  - `name`: Tên của mô hình AI (string)
  - `version`: Phiên bản của mô hình AI (string)
  - `file`: Tệp mô hình AI (binary)
- **Success Response (200 OK):**

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "CROP",
    "file_path": "path/to/stored/file",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `POST /models/embedding`

- **Mô tả:** Tải lên một tệp mô hình AI mới thuộc loại EMBEDDING và lưu trữ metadata của nó.
- **Request Body:** `multipart/form-data`
  - `name`: Tên của mô hình AI (string)
  - `version`: Phiên bản của mô hình AI (string)
  - `file`: Tệp mô hình AI (binary)
- **Success Response (200 OK):**

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "EMBEDDING",
    "file_path": "path/to/stored/file",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `GET /models/latest/crop`

- **Mô tả:** Lấy thông tin về mô hình CROP mới nhất.
- **Success Response (200 OK):**

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "CROP",
    "file_path": "path/to/stored/file",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `GET /models/latest/embedding`

- **Mô tả:** Lấy thông tin về mô hình EMBEDDING mới nhất.
- **Success Response (200 OK):**

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "EMBEDDING",
    "file_path": "path/to/stored/file",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `GET /models/crop`

- **Mô tả:** Liệt kê tất cả các mô hình AI thuộc loại CROP.
- **Success Response (200 OK):**

  ```json
  {
    "models": [
      {
        "id": "model-uuid",
        "name": "string",
        "version": "string",
        "model_type": "CROP",
        "file_path": "path/to/stored/file",
        "uploaded_at": "2025-08-30T10:00:00Z"
      }
    ]
  }
  ```

### `GET /models/embedding`

- **Mô tả:** Liệt kê tất cả các mô hình AI thuộc loại EMBEDDING.
- **Success Response (200 OK):**

  ```json
  {
    "models": [
      {
        "id": "model-uuid",
        "name": "string",
        "version": "string",
        "model_type": "EMBEDDING",
        "file_path": "path/to/stored/file",
        "uploaded_at": "2025-08-30T10:00:00Z"
      }
    ]
  }
  ```

### `GET /models/{model_id}/download`

- **Mô tả:** Tải xuống một tệp mô hình AI dựa trên ID của nó.
- **URL Params:** `model_id` (UUID, required).
- **Success Response (200 OK):** Trả về tệp mô hình AI dưới dạng `application/octet-stream`.

### `DELETE /models/{model_id}`

- **Mô tả:** Xóa một tệp mô hình AI và metadata của nó dựa trên ID.
- **URL Params:** `model_id` (UUID, required).
- **Success Response (204 No Content):** Không có nội dung trả về.

---

## 8. Product Vector API (`/vectors`)

Cung cấp các chức năng để quản lý và tải xuống các vector sản phẩm.

### `GET /vectors/download`

- **Mô tả:** Tải xuống tất cả các vector sản phẩm từ cơ sở dữ liệu để sử dụng phía client.
- **Success Response (200 OK):**

  ```json
  {
    "vectors": [
      {
        "product_id": "product-uuid",
        "model_id": "model-uuid",
        "embedding": [0.1, 0.2, ..., 0.N]
      }
    ]
  }
  ```

---

## 8. Debug API (`/debug`)

API chỉ dùng cho mục đích phát triển và kiểm thử.

### `POST /debug/prepare-cart`

- **Mô tả:** Chuẩn bị nhanh một giỏ hàng test. API sẽ tự động tìm một phiên mua hàng đang hoạt động của người dùng (hoặc tạo mới), xóa các sản phẩm cũ và thêm một sản phẩm mẫu vào đó.
- **Yêu cầu:** Xác thực JWT của người dùng.
- **Success Response (200 OK):** `{ "message": "Giỏ hàng đã sẵn sàng để checkout." }`
