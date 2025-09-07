# Data Schema (Updated)

Tài liệu này định nghĩa cấu trúc dữ liệu đã được cập nhật cho hệ thống Giỏ hàng thông minh.

---

## 1. Core Tables (Bảng lõi)

### `Users`

Lưu trữ thông tin người dùng.

| Tên cột        | Kiểu dữ liệu | Khóa   | Ghi chú                                  |
| :-------------- | :----------- | :----- | :--------------------------------------- |
| `id`            | UUID         | PK     | Khóa chính, tự động tạo                  |
| `full_name`     | VARCHAR(255) |        | Tên đầy đủ của người dùng                |
| `email`         | VARCHAR(255) | UNIQUE | Email, dùng để đăng nhập                 |
| `password_hash` | VARCHAR(255) |        | Mật khẩu đã được băm                     |
| `created_at`    | TIMESTAMPTZ  |        | Thời gian tạo                            |
| `updated_at`    | TIMESTAMPTZ  |        | Thời gian cập nhật lần cuối              |

### `Products`

Lưu trữ thông tin cơ bản về các sản phẩm.

| Tên cột        | Kiểu dữ liệu   | Khóa   | Ghi chú                                     |
| :------------- | :------------- | :----- | :------------------------------------------ |
| `id`           | UUID           | PK     | Khóa chính                                  |
| `name`         | VARCHAR(255)   |        | Tên sản phẩm                                |
| `description`  | TEXT           |        | Mô tả chi tiết sản phẩm                     |
| `price`        | DECIMAL(10, 2) |        | Giá bán                                     |
| `weight_grams` | INTEGER        |        | Cân nặng sản phẩm (gram), dùng cho cảm biến |
| `created_at`   | TIMESTAMPTZ    |        |                                             |
| `updated_at`   | TIMESTAMPTZ    |        |                                             |

### `Product_Images`

Lưu trữ nhiều hình ảnh cho một sản phẩm.

| Tên cột     | Kiểu dữ liệu | Khóa | Ghi chú                                                              |
| :---------- | :----------- | :--- | :------------------------------------------------------------------- |
| `id`        | UUID         | PK   | Khóa chính                                                           |
| `product_id`| UUID         | FK   | Liên kết tới `Products.id`                                           |
| `image_url` | VARCHAR(255) |      | Khóa đối tượng (object key) của file trên Cloudflare R2 (ví dụ: `images/products/uuid.jpg`) |
| `is_primary`| BOOLEAN      |      | `True` nếu là ảnh đại diện (thumbnail)                               |

---

## 2. Product Organization (Tổ chức sản phẩm)

### `Categories`

Lưu trữ danh mục sản phẩm, hỗ trợ cấu trúc cha-con.

| Tên cột     | Kiểu dữ liệu | Khóa   | Ghi chú                               |
| :---------- | :----------- | :----- | :------------------------------------ |
| `id`        | UUID         | PK     | Khóa chính                            |
| `name`      | VARCHAR(255) |        | Tên danh mục                          |
| `parent_id` | UUID         | FK     | Liên kết tới `Categories.id` (tự trỏ) |

### `Product_Categories`

Bảng nối nhiều-nhiều giữa sản phẩm và danh mục.

| Tên cột       | Kiểu dữ liệu | Khóa | Ghi chú                     |
| :------------ | :----------- | :--- | :-------------------------- |
| `product_id`  | UUID         | FK   | Liên kết tới `Products.id`  |
| `category_id` | UUID         | FK   | Liên kết tới `Categories.id` |

---

## 3. User Interaction (Tương tác người dùng)

### `Product_Reviews`

Lưu trữ đánh giá và bình luận của người dùng về sản phẩm.

| Tên cột     | Kiểu dữ liệu | Khóa | Ghi chú                     |
| :---------- | :----------- | :--- | :-------------------------- |
| `id`        | UUID         | PK   | Khóa chính                  |
| `product_id`| UUID         | FK   | Liên kết tới `Products.id`  |
| `user_id`   | UUID         | FK   | Liên kết tới `Users.id`     |
| `rating`    | INTEGER      |      | Điểm đánh giá (1-5)         |
| `comment`   | TEXT         |      | Nội dung bình luận          |
| `created_at`| TIMESTAMPTZ  |      |                             |

### `User_Favorites`

Bảng nối nhiều-nhiều cho các sản phẩm yêu thích của người dùng.

| Tên cột      | Kiểu dữ liệu | Khóa | Ghi chú                    |
| :----------- | :----------- | :--- | :------------------------- |
| `user_id`    | UUID         | FK   | Liên kết tới `Users.id`    |
| `product_id` | UUID         | FK   | Liên kết tới `Products.id` |

### `Notifications`

Lưu trữ thông báo gửi đến người dùng.

| Tên cột     | Kiểu dữ liệu | Khóa | Ghi chú                  |
| :---------- | :----------- | :--- | :----------------------- |
| `id`        | UUID         | PK   | Khóa chính               |
| `user_id`   | UUID         | FK   | Liên kết tới `Users.id`  |
| `title`     | VARCHAR(255) |      | Tiêu đề thông báo        |
| `message`   | TEXT         |      | Nội dung thông báo       |
| `is_read`   | BOOLEAN      |      | Trạng thái đã đọc        |
| `created_at`| TIMESTAMPTZ  |      |                             |

---

## 4. Shopping & Checkout (Mua sắm & Thanh toán)

### `Shopping_Sessions`

Quản lý một phiên mua sắm của người dùng.

| Tên cột      | Kiểu dữ liệu | Khóa | Ghi chú                                      |
| :----------- | :----------- | :--- | :------------------------------------------- |
| `id`         | UUID         | PK   | Khóa chính của phiên (`sessionId`)           |
| `user_id`    | UUID         | FK   | Liên kết tới `Users.id`                      |
| `status`     | VARCHAR(50)  |      | Trạng thái: `active`, `completed`, `abandoned` |
| `created_at` | TIMESTAMPTZ  |      |                                              |

### `Shopping_Session_Items`

Lưu các sản phẩm trong giỏ hàng của một phiên đang hoạt động.

| Tên cột      | Kiểu dữ liệu | Khóa | Ghi chú                                |
| :----------- | :----------- | :--- | :------------------------------------- |
| `id`         | UUID         | PK   | Khóa chính                             |
| `session_id` | UUID         | FK   | Liên kết tới `Shopping_Sessions.id`    |
| `product_id` | UUID         | FK   | Liên kết tới `Products.id`             |
| `quantity`   | INTEGER      |      | Số lượng sản phẩm                      |
| `added_at`   | TIMESTAMPTZ  |      | Thời điểm thêm vào giỏ                 |

### `Orders`

Lưu thông tin các đơn hàng đã thanh toán.

| Tên cột          | Kiểu dữ liệu   | Khóa | Ghi chú                                      |
| :--------------- | :------------- | :--- | :------------------------------------------- |
| `id`             | UUID           | PK   | Khóa chính của đơn hàng                      |
| `session_id`     | UUID           | FK   | Liên kết tới `Shopping_Sessions.id` (Bắt buộc) |
| `total_amount`   | DECIMAL(12, 2) |      | Tổng số tiền của đơn hàng                    |
| `payment_method` | VARCHAR(50)    |      | Ví dụ: "payos_webhook"                       |
| `status`         | VARCHAR(50)    |      | `pending`, `completed`, `failed`             |
| `gateway_txn_id` | VARCHAR(255)   |      | ID của giao dịch từ cổng thanh toán          |
| `created_at`     | TIMESTAMPTZ    |      |                                              |
| `updated_at`     | TIMESTAMPTZ    |      |                                              |

### `Order_Items`

Lưu chi tiết các sản phẩm trong một đơn hàng đã hoàn tất.

| Tên cột             | Kiểu dữ liệu   | Khóa | Ghi chú                               |
| :------------------ | :------------- | :--- | :------------------------------------ |
| `id`                | UUID           | PK   | Khóa chính                            |
| `order_id`          | UUID           | FK   | Liên kết tới `Orders.id`              |
| `product_id`        | UUID           | FK   | Liên kết tới `Products.id`            |
| `quantity`          | INTEGER        |      | Số lượng sản phẩm                     |
| `price_at_purchase` | DECIMAL(10, 2) |      | Giá sản phẩm tại thời điểm mua hàng   |

### `Order_Code_Lookup`

**Bảng mới**: Dùng để map giữa `order_code` (dạng số, của cổng thanh toán) và `order_id` (dạng UUID, của hệ thống).

| Tên cột      | Kiểu dữ liệu | Khóa   | Ghi chú                               |
| :----------- | :----------- | :----- | :------------------------------------ |
| `order_code` | INTEGER      | PK     | Mã đơn hàng dạng số gửi cho PayOS    |
| `order_id`   | UUID         | FK     | Liên kết tới `Orders.id`              |
| `created_at` | TIMESTAMPTZ  |        | Thời gian tạo                         |

---

## 5. Promotions & Auth (Khuyến mãi & Xác thực)

### `Promotions`

Lưu trữ thông tin các chương trình khuyến mãi.

| Tên cột          | Kiểu dữ liệu   | Khóa | Ghi chú                                  |
| :--------------- | :------------- | :--- | :--------------------------------------- |
| `id`             | UUID           | PK   | Khóa chính                               |
| `name`           | VARCHAR(255)   |      | Tên chương trình khuyến mãi              |
| `description`    | TEXT           |      | Mô tả chi tiết                           |
| `discount_type`  | VARCHAR(50)    |      | `percentage` hoặc `fixed_amount`         |
| `discount_value` | DECIMAL(10, 2) |      | Giá trị khuyến mãi                       |
| `start_date`     | TIMESTAMPTZ    |      | Ngày bắt đầu                             |
| `end_date`       | TIMESTAMPTZ    |      | Ngày kết thúc                            |
| `is_active`      | BOOLEAN        |      | Trạng thái kích hoạt                      |

### `Promotion_Products` và `Promotion_Categories`

Bảng nối để áp dụng khuyến mãi cho sản phẩm hoặc danh mục cụ thể.

| Tên cột         | Kiểu dữ liệu | Khóa | Ghi chú                       |
| :-------------- | :----------- | :--- | :---------------------------- |
| `promotion_id`  | UUID         | FK   | Liên kết tới `Promotions.id`  |
| `product_id`    | UUID         | FK   | Liên kết tới `Products.id`    |
| `category_id`   | UUID         | FK   | Liên kết tới `Categories.id`  |

### `QR_Auth_Tokens`

Lưu trữ token dùng cho việc đăng nhập nhanh bằng mã QR.

| Tên cột               | Kiểu dữ liệu | Khóa   | Ghi chú                                         |
| :-------------------- | :----------- | :----- | :---------------------------------------------- |
| `id`                  | UUID         | PK     | Khóa chính                                      |
| `token`               | VARCHAR(255) | UNIQUE | Chuỗi token duy nhất                            |
| `user_id`             | UUID         | FK     | Liên kết tới `Users.id` (cập nhật sau khi quét) |
| `shopping_session_id` | UUID         | FK     | Liên kết tới `Shopping_Sessions.id` (sau khi quét) |
| `status`              | VARCHAR(50)  |        | `pending`, `authenticated`, `expired`           |
| `expires_at`          | TIMESTAMP    |        | Thời gian token hết hạn                         |
| `created_at`          | TIMESTAMPTZ  |        |                                                 |

---

## 6. AI Models

Lưu trữ metadata của các mô hình AI.

| Tên cột       | Kiểu dữ liệu | Khóa   | Ghi chú                                                              |
| :------------ | :----------- | :----- | :------------------------------------------------------------------- |
| `id`          | UUID         | PK     | Khóa chính                                                           |
| `model_type`  | VARCHAR(50)  |        | Loại mô hình (CROP, EMBEDDING)                                       |
| `name`        | VARCHAR(255) |        | Tên mô hình AI                                                       |
| `version`     | VARCHAR(50)  |        | Phiên bản mô hình                                                    |
| `file_path`   | VARCHAR(512) | UNIQUE | Khóa đối tượng (object key) của file model trên Cloudflare R2 (ví dụ: `models/crop/uuid.bin`) |
| `uploaded_at` | TIMESTAMPTZ  |        | Thời gian tải lên                                                    |

### `Product_Vectors`

**Bảng mới**: Lưu trữ các vector nhúng của sản phẩm, được tạo ra từ các mô hình AI.

| Tên cột     | Kiểu dữ liệu | Khóa | Ghi chú                               |
| :---------- | :----------- | :--- | :------------------------------------ |
| `id`        | UUID         | PK   | Khóa chính                            |
| `product_id`| UUID         | FK   | Liên kết tới `Products.id`            |
| `model_id`  | UUID         | FK   | Liên kết tới `AI_Models.id`           |
| `image_id`  | UUID         | FK   | Liên kết tới `Product_Images.id`      |
| `embedding` | JSON         |      | Mảng các số thực biểu diễn vector nhúng |
| `created_at`| TIMESTAMPTZ  |      | Thời gian tạo                         |

---
