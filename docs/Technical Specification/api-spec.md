# API Specification (Updated)

## 1. Thông tin chung

- **Authentication:** Hầu hết các endpoint yêu cầu xác thực đều sử dụng **Bearer Token (JWT)** được gửi qua `Authorization` header. Người dùng lấy token này từ API `POST /auth/login`.
- **Định dạng dữ liệu:** JSON
- **Lưu trữ file:** Các file (hình ảnh sản phẩm, model AI) được lưu trữ trên **Cloudflare R2**. Các URL trả về từ API là các URL công khai đầy đủ, sẵn sàng sử dụng.
  - **Cấu trúc thư mục ảo trên R2:**
    - Hình ảnh sản phẩm: `images/products/<UUID_duy_nhat>.<phan_mo_rong_file>`
    - Model AI CROP: `models/crop/<ten_model>-<phien_ban_model>-<UUID_duy_nhat>.<phan_mo_rong_file>`
    - Model AI EMBEDDING: `models/embedding/<ten_model>-<phien_ban_model>-<UUID_duy_nhat>.<phan_mo_rong_file>`
  - **Biến môi trường:** `CLOUDFLARE_R2_PUBLIC_URL` được sử dụng để cấu hình phần gốc của URL công khai (ví dụ: `https://pub-xxxxxxxx.r2.dev/` hoặc `https://cdn.yourdomain.com/`).

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
- **Success Response (200 OK):}

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
- **Success Response (200 OK):}

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

- **Success Response (200 OK):}

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
- **Success Response (200 OK):}

  ```json
  {
    "status": "pending | authenticated | expired",
    "user": { ... } // (null nếu chưa authenticated)
  }
  ```

### `GET /sessions/{session_id}`

- **Mô tả:** Lấy thông tin chi tiết của một phiên mua sắm, bao gồm danh sách các mặt hàng hiện có trong giỏ. Yêu cầu xác thực và chỉ người dùng sở hữu phiên mới có quyền truy cập.
- **URL Params:** `session_id` (UUID, required).
- **Yêu cầu:** Xác thực JWT của người dùng.
- **Success Response (200 OK):** Trả về thông tin phiên mua sắm, tương tự như response của `PATCH /sessions/{session_id}/items`.

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
          "price": 100.00,
          "primary_image": {
            "id": "image-uuid",
            "image_url": "https://.../image.jpg",
            "is_primary": true
          }
        }
      }
    ]
  }
  ```

### `PATCH /sessions/{session_id}/items`

- **Mô tả:** Cập nhật các mặt hàng trong một phiên mua sắm. Endpoint này cho phép thêm sản phẩm mới, cập nhật số lượng sản phẩm đã có, hoặc xóa sản phẩm khỏi giỏ (bằng cách gửi số lượng là 0).
- **URL Params:** `session_id` (UUID, required).
- **Request Body:**

  ```json
  {
    "items": [
      {
        "product_id": "product-uuid-1",
        "quantity": 2
      },
      {
        "product_id": "product-uuid-2",
        "quantity": 0
      }
    ]
  }
  ```

- **Success Response (200 OK):} Trả về toàn bộ thông tin phiên mua sắm đã được cập nhật.

  ```json
  {
    "id": "session-uuid",
    "user_id": "user-uuid",
    "status": "active",
    "created_at": "2025-08-30T10:00:00Z",
    "items": [
      {
        "id": "item-uuid",
        "product_id": "product-uuid-1",
        "quantity": 2,
        "added_at": "2025-08-30T10:00:00Z",
        "product": {
          "id": "product-uuid-1",
          "name": "Tên sản phẩm 1",
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

- **Success Response (200 OK):} Trả về ID đơn hàng và URL thanh toán để hiển thị QR.

  ```json
  {
    "order_id": "order-uuid",
    "payment_qr_url": "https://link-or-qr-image-url.com/pay?order_id=..."
  }
  ```

### `GET /checkout/status/{order_id}`

- **Mô tả:** Client gọi để kiểm tra trạng thái của đơn hàng sau khi người dùng quét mã QR.
- **URL Params:** `order_id` (UUID, required).
- **Success Response (200 OK):}

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
- **Success Response (200 OK):} `{ "status": "success" }`

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

### `POST /products/`

- **Mô tả:** Tạo một sản phẩm mới với thông tin cơ bản và liên kết nó với các danh mục.
- **Request Body:**

  ```json
  {
    "name": "Tên sản phẩm mới",
    "description": "Mô tả chi tiết về sản phẩm.",
    "price": 99.99,
    "weight_grams": 500,
    "category_ids": ["uuid-danh-muc-1", "uuid-danh-muc-2"]
  }
  ```

- **Success Response (201 Created):}

  ```json
  {
    "id": "uuid-san-pham-moi",
    "name": "Tên sản phẩm mới",
    "description": "Mô tả chi tiết về sản phẩm.",
    "price": 99.99,
    "weight_grams": 500,
    "created_at": "2025-09-05T10:00:00Z",
    "updated_at": "2025-09-05T10:00:00Z",
    "categories": [
      {
        "id": "category-uuid",
        "name": "Tên danh mục",
        "parent_id": null
      }
    ],
    "primary_image": null
  }
  ```

### `GET /products/{product_id}`

- **Mô tả:** Lấy thông tin chi tiết của một sản phẩm cụ thể bằng ID của nó, bao gồm hình ảnh và danh mục.
- **URL Params:** `product_id` (UUID, required).
- **Success Response (200 OK):}

  ```json
  {
    "id": "product-uuid",
    "name": "Tên sản phẩm",
    "description": "Mô tả sản phẩm",
    "price": 50.00,
    "weight_grams": 1000,
    "created_at": "2025-09-05T10:00:00Z",
    "updated_at": "2025-09-05T10:00:00Z",
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
      "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
      "is_primary": true
    }
  }
  ```

### `PATCH /products/{product_id}`

- **Mô tả:** Cập nhật thông tin cơ bản và liên kết danh mục của một sản phẩm hiện có.
- **URL Params:** `product_id` (UUID, required).
- **Request Body:** (Các trường là tùy chọn, chỉ gửi những trường muốn cập nhật)

  ```json
  {
    "name": "Tên sản phẩm đã cập nhật",
    "price": 120.00,
    "category_ids": ["uuid-danh-muc-moi"]
  }
  ```

- **Success Response (200 OK):} Trả về thông tin sản phẩm đã cập nhật.

  ```json
  {
    "id": "product-uuid",
    "name": "Tên sản phẩm đã cập nhật",
    "description": "Mô tả sản phẩm",
    "price": 120.00,
    "weight_grams": 1000,
    "created_at": "2025-09-05T10:00:00Z",
    "updated_at": "2025-09-05T10:30:00Z",
    "categories": [
      {
        "id": "category-uuid",
        "name": "Tên danh mục mới",
        "parent_id": null
      }
    ],
    "primary_image": {
      "id": "image-uuid",
      "product_id": "product-uuid",
      "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
      "is_primary": true
    }
  }
  ```

### `DELETE /products/{product_id}`

- **Mô tả:** Xóa một sản phẩm và tất cả dữ liệu liên quan của nó (hình ảnh từ R2, đánh giá, yêu thích, v.v.). Không xóa các bản ghi `OrderItem` vì mục đích lịch sử.
- **URL Params:** `product_id` (UUID, required).
- **Success Response (204 No Content):} Không có nội dung trả về.

### `GET /products/`

- **Mô tả:** Tìm kiếm và lọc sản phẩm.
- **Query Params:**
  - `query` (string, optional): Chuỗi tìm kiếm theo tên và mô tả sản phẩm.
  - `category_id` (UUID, optional): Lọc sản phẩm theo ID danh mục.
  - `min_price` (float, optional): Giá tối thiểu.
  - `max_price` (float, optional): Giá tối đa.
  - `skip` (int, optional, default: 0): Bỏ qua bao nhiêu sản phẩm đầu tiên (để phân trang).
  - `limit` (int, optional, default: 100): Giới hạn số lượng sản phẩm trả về.
- **Success Response (200 OK):}

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
          "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
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
- **Success Response (200 OK):}

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
- **Success Response (200 OK):}

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
          "primary_image": {
            "id": "image-uuid",
            "product_id": "product-uuid",
            "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
            "is_primary": true
          }
        },
        {
          "id": "product-uuid-b",
          "name": "Pepsi",
          "price": 10.00,
          "total_quantity_sold": 120,
          "primary_image": {
            "id": "image-uuid",
            "product_id": "product-uuid",
            "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
            "is_primary": true
          }
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
          "primary_image": {
            "id": "image-uuid",
            "product_id": "product-uuid",
            "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
            "is_primary": true
          }
        },
        {
          "id": "product-uuid-d",
          "name": "Lay's Stax",
          "price": 20.00,
          "total_quantity_sold": 180,
          "primary_image": {
            "id": "image-uuid",
            "product_id": "product-uuid",
            "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
            "is_primary": true
          }
        }
      ]
    }
  ]
  ```

### `GET /products/{product_id}/images`

- **Mô tả:** Lấy tất cả hình ảnh liên quan đến một sản phẩm cụ thể.
- **URL Params:** `product_id` (UUID, required).
- **Success Response (200 OK):}

  ```json
  {
    "images": [
      {
        "id": "image-uuid",
        "product_id": "product-uuid",
        "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
        "is_primary": true
      }
    ]
  }
  ```

### `POST /products/{product_id}/images`

- **Mô tả:** Thêm một hình ảnh mới cho sản phẩm bằng cách tải file lên Cloudflare R2. Nếu `is_primary` là `true`, bất kỳ hình ảnh chính hiện có nào của sản phẩm đó sẽ bị gỡ bỏ.
- **URL Params:** `product_id` (UUID, required).
- **Request Body:** `multipart/form-data`
  - `file`: Tệp hình ảnh (binary, required). Hỗ trợ các định dạng ảnh phổ biến.
  - `is_primary`: Đặt là `true` nếu đây là hình ảnh chính của sản phẩm (boolean, optional, default: `false`).
- **Success Response (201 Created):}

  ```json
  {
    "id": "image-uuid",
    "product_id": "product-uuid",
    "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
    "is_primary": true
  }
  ```

### `DELETE /products/images/{image_id}`

- **Mô tả:** Xóa một hình ảnh sản phẩm cụ thể bằng ID của nó. File cũng sẽ được xóa khỏi Cloudflare R2.
- **URL Params:** `image_id` (UUID, required).
- **Success Response (204 No Content):} Không có nội dung trả về.

### `PUT /products/images/{image_id}/set-primary`

- **Mô tả:** Đặt một hình ảnh cụ thể làm hình ảnh chính cho sản phẩm của nó. Bất kỳ hình ảnh chính nào khác cho cùng một sản phẩm sẽ bị gỡ bỏ.
- **URL Params:** `image_id` (UUID, required).
- **Success Response (200 OK):}

  ```json
  {
    "id": "image-uuid",
    "product_id": "product-uuid",
    "image_url": "https://pub-xxxxxxxx.r2.dev/images/products/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
    "is_primary": true
  }
  ```

---

## 7. AI Model Management API (`/models`)

Cung cấp các chức năng để tải lên, tải xuống, liệt kê và xóa các mô hình AI.

### `POST /models/crop`

- **Mô tả:** Tải lên một tệp mô hình AI mới thuộc loại CROP lên Cloudflare R2 và lưu trữ metadata của nó.
- **Request Body:** `multipart/form-data`
  - `name`: Tên của mô hình AI (string)
  - `version`: Phiên bản của mô hình AI (string)
  - `file`: Tệp mô hình AI (binary)
- **Success Response (200 OK):}

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "CROP",
    "file_path": "https://pub-xxxxxxxx.r2.dev/models/crop/MyCropModel-1.0-uuid.bin",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `POST /models/embedding`

- **Mô tả:** Tải lên một tệp mô hình AI mới thuộc loại EMBEDDING lên Cloudflare R2 và lưu trữ metadata của nó.
- **Request Body:** `multipart/form-data`
  - `name`: Tên của mô hình AI (string)
  - `version`: Phiên bản của mô hình AI (string)
  - `file`: Tệp mô hình AI (binary)
- **Success Response (200 OK):}

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "EMBEDDING",
    "file_path": "https://pub-xxxxxxxx.r2.dev/models/embedding/MyEmbeddingModel-1.0-uuid.bin",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `GET /models/latest/crop`

- **Mô tả:** Lấy thông tin về mô hình CROP mới nhất.
- **Success Response (200 OK):}

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "CROP",
    "file_path": "https://pub-xxxxxxxx.r2.dev/models/crop/MyCropModel-1.0-uuid.bin",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `GET /models/latest/embedding`

- **Mô tả:** Lấy thông tin về mô hình EMBEDDING mới nhất.
- **Success Response (200 OK):}

  ```json
  {
    "id": "model-uuid",
    "name": "string",
    "version": "string",
    "model_type": "EMBEDDING",
    "file_path": "https://pub-xxxxxxxx.r2.dev/models/embedding/MyEmbeddingModel-1.0-uuid.bin",
    "uploaded_at": "2025-08-30T10:00:00Z"
  }
  ```

### `GET /models/crop`

- **Mô tả:** Liệt kê tất cả các mô hình AI thuộc loại CROP.
- **Success Response (200 OK):}

  ```json
  {
    "models": [
      {
        "id": "model-uuid",
        "name": "string",
        "version": "string",
        "model_type": "CROP",
        "file_path": "https://pub-xxxxxxxx.r2.dev/models/crop/MyCropModel-1.0-uuid.bin",
        "uploaded_at": "2025-08-30T10:00:00Z"
      }
    ]
  }
  ```

### `GET /models/embedding`

- **Mô tả:** Liệt kê tất cả các mô hình AI thuộc loại EMBEDDING.
- **Success Response (200 OK):}

  ```json
  {
    "models": [
      {
        "id": "model-uuid",
        "name": "string",
        "version": "string",
        "model_type": "EMBEDDING",
        "file_path": "https://pub-xxxxxxxx.r2.dev/models/embedding/MyEmbeddingModel-1.0-uuid.bin",
        "uploaded_at": "2025-08-30T10:00:00Z"
      }
    ]
  }
  ```

### `GET /models/{model_id}/download`

- **Mô tả:** Tải xuống một tệp mô hình AI dựa trên ID của nó. API sẽ chuyển hướng đến URL công khai của file trên Cloudflare R2.
- **URL Params:** `model_id` (UUID, required).
- **Success Response (302 Found):} Chuyển hướng đến URL của file trên Cloudflare R2.

### `DELETE /models/{model_id}`

- **Mô tả:** Xóa một tệp mô hình AI khỏi Cloudflare R2 và metadata của nó dựa trên ID.
- **URL Params:** `model_id` (UUID, required).
- **Success Response (204 No Content):} Không có nội dung trả về.

---

## 8. Product Vector API (`/vectors`)

Cung cấp các chức năng để quản lý và tải xuống các vector sản phẩm.

### `GET /vectors/download`

- **Mô tả:** Tải xuống tất cả các vector sản phẩm từ cơ sở dữ liệu dưới dạng một file JSON. File này chỉ chứa `product_id` và `embedding` của mỗi vector.
- **Success Response (200 OK):} (File tải xuống: `product_vectors.json`)

  ```json
  {
    "vectors": [
      {
        "product_id": "product-uuid",
        "embedding": [0.1, 0.2, ..., 0.N]
      }
    ]
  }
  ```

---

### `GET /vectors/last-updated`

- **Mô tả:** Lấy thời gian tạo của vector sản phẩm mới nhất. Client có thể dùng endpoint này để kiểm tra xem có dữ liệu vector mới cần tải xuống hay không.
- **Success Response (200 OK):}

  ```json
  {
    "last_updated": "2025-09-06T14:30:00.123Z"
  }
  ```

---

## 8. Debug API (`/debug`)

API chỉ dùng cho mục đích phát triển và kiểm thử.

### `POST /debug/prepare-cart`

- **Mô tả:** Chuẩn bị nhanh một giỏ hàng test. API sẽ tự động tìm một phiên mua hàng đang hoạt động của người dùng (hoặc tạo mới), xóa các sản phẩm cũ và thêm một sản phẩm mẫu vào đó.
- **Yêu cầu:** Xác thực JWT của người dùng.
- **Success Response (200 OK):} `{ "message": "Giỏ hàng đã sẵn sàng để checkout." }`
esponse (200 OK):} `{ "message": "Giỏ hàng đã sẵn sàng để checkout." }`

---

## 9. Banner API (`/banners`)

Cung cấp các chức năng để quản lý banner quảng cáo.

### `POST /banners/upload`

- **Mô tả:** Tải lên một banner mới. Yêu cầu quyền admin.
- **Request Body:** `multipart/form-data`
  - `title`: Tiêu đề của banner (string, required).
  - `target_url`: URL mà banner sẽ trỏ đến khi được nhấp vào (string, optional).
  - `is_active`: Trạng thái của banner (boolean, optional, default: `true`).
  - `file`: Tệp hình ảnh (binary, required).
- **Success Response (201 Created):**

  ```json
  {
    "id": "banner-uuid",
    "title": "Tiêu đề banner",
    "image_url": "https://pub-xxxxxxxx.r2.dev/images/banners/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
    "target_url": "https://example.com/promotion",
    "is_active": true,
    "created_at": "2025-09-07T10:00:00Z"
  }
  ```

### `GET /banners/active`

- **Mô tả:** Lấy danh sách tất cả các banner đang hoạt động.
- **Success Response (200 OK):**

  ```json
  {
    "banners": [
      {
        "id": "banner-uuid",
        "title": "Tiêu đề banner",
        "image_url": "https://pub-xxxxxxxx.r2.dev/images/banners/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
        "target_url": "https://example.com/promotion",
        "is_active": true,
        "created_at": "2025-09-07T10:00:00Z"
      }
    ]
  }
  ```

### `GET /banners/`

- **Mô tả:** Lấy danh sách tất cả các banner (dành cho admin).
- **Yêu cầu:** Xác thực JWT của admin.
- **Success Response (200 OK):** Tương tự như `GET /banners/active`.

### `GET /banners/{banner_id}`

- **Mô tả:** Lấy thông tin chi tiết của một banner bằng ID.
- **URL Params:** `banner_id` (UUID, required).
- **Success Response (200 OK):**

  ```json
  {
    "id": "banner-uuid",
    "title": "Tiêu đề banner",
    "image_url": "https://pub-xxxxxxxx.r2.dev/images/banners/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
    "target_url": "https://example.com/promotion",
    "is_active": true,
    "created_at": "2025-09-07T10:00:00Z"
  }
  ```

### `PATCH /banners/{banner_id}`

- **Mô tả:** Cập nhật thông tin của một banner. Yêu cầu quyền admin.
- **URL Params:** `banner_id` (UUID, required).
- **Request Body:** (Các trường là tùy chọn)

  ```json
  {
    "title": "Tiêu đề banner mới",
    "is_active": false
  }
  ```

- **Success Response (200 OK):** Trả về thông tin banner đã được cập nhật.

### `DELETE /banners/{banner_id}`

- **Mô tả:** Xóa một banner. Yêu cầu quyền admin.
- **URL Params:** `banner_id` (UUID, required).
- **Success Response (204 No Content):** Không có nội dung trả về.
