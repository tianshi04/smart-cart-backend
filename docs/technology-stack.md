# Backend Technology Stack

Tài liệu này mô tả chi tiết về các công nghệ được lựa chọn để xây dựng hệ thống backend cho dự án Giỏ hàng thông minh.

## 1. Nền tảng chính

- **Ngôn ngữ: Python 3.12**
  - **Lý do:** Đây là một phiên bản Python hiện đại, mang lại những cải tiến đáng kể về hiệu năng so với các phiên bản trước (nhờ dự án "Faster CPython"). Việc sử dụng phiên bản mới nhất đảm bảo sự hỗ trợ lâu dài và cho phép tận dụng các tính năng ngôn ngữ mới nhất để viết code hiệu quả hơn.

- **Framework: FastAPI**
  - **Lý do:** FastAPI là một web framework hiệu năng cao, được xây dựng dựa trên Starlette và Pydantic. Lựa chọn này dựa trên các ưu điểm chính sau:
    - **Hỗ trợ bất đồng bộ (Async):** Cực kỳ quan trọng cho các endpoint long-polling (`/listen`) của dự án, giúp xử lý hiệu quả hàng nghìn kết nối đồng thời từ các xe đẩy mà không tiêu tốn nhiều tài nguyên.
    - **Tốc độ:** Là một trong những framework Python nhanh nhất hiện có.
    - **Validation dữ liệu:** Tích hợp Pydantic để tự động xác thực, tuần tự hóa (serialize) và tạo tài liệu cho dữ liệu dựa trên type hints của Python. Điều này giúp giảm thiểu code soạn sẵn (boilerplate) và đảm bảo dữ liệu đầu vào luôn hợp lệ.
    - **Tài liệu API tự động:** Tự động sinh ra giao diện tài liệu API tương tác (Swagger UI, ReDoc), giúp các đội phát triển client (Mobile App, Smart Cart) dễ dàng hiểu và sử dụng API.

## 2. Cơ sở dữ liệu và Tương tác

- **Hệ quản trị CSDL: PostgreSQL**
  - **Lý do:** Là một hệ quản trị CSDL quan hệ mã nguồn mở mạnh mẽ, đáng tin cậy và đã được chứng minh trong thực tế. Nó hỗ trợ đầy đủ các kiểu dữ liệu cần thiết cho schema của dự án (UUID, TIMESTAMPTZ) và có khả năng mở rộng tốt.

- **ORM (Object-Relational Mapper): SQLAlchemy 2.0**
  - **Lý do:** Là thư viện ORM tiêu chuẩn của Python, cho phép ánh xạ các bảng CSDL thành các lớp Python một cách rõ ràng. Phiên bản 2.0 hỗ trợ hoàn toàn `asyncio`, giúp tích hợp liền mạch với FastAPI và cho phép thực hiện các truy vấn CSDL một cách bất đồng bộ.

- **Database Migrations: Alembic**
  - **Lý do:** Là công cụ đi kèm với SQLAlchemy, cung cấp một cơ chế vững chắc để quản lý các thay đổi về cấu trúc CSDL (schema migrations) theo thời gian. Mọi thay đổi (thêm bảng, sửa cột) đều được quản lý dưới dạng các file script có phiên bản, đảm bảo tính nhất quán trên mọi môi trường.

## 3. Triển khai (Deployment)

- **Web Server: Uvicorn**
  - **Lý do:** Là một máy chủ ASGI (Asynchronous Server Gateway Interface) hiệu năng cao, được khuyến nghị chính thức để chạy các ứng dụng FastAPI.

- **Containerization: Docker & Docker Compose**
  - **Lý do:** Đóng gói ứng dụng và các dịch vụ phụ thuộc (như PostgreSQL) vào các container độc lập. Điều này đảm bảo môi trường phát triển và sản xuất là đồng nhất, đơn giản hóa quá trình thiết lập và triển khai.

## 4. Xác thực

- **Cơ chế: JSON Web Tokens (JWT)**
  - **Lý do:** JWT là một tiêu chuẩn mở, an toàn để truyền thông tin giữa các bên dưới dạng một đối tượng JSON. Nó phù hợp cho việc xác thực người dùng trên Mobile App, cho phép tạo ra các token có thời gian hết hạn và không cần lưu trữ trạng thái phiên trên server.

## 5. Tích hợp thanh toán

- **Cổng thanh toán: PayOS**
  - **Lý do:** Được lựa chọn để xử lý các giao dịch thanh toán. Backend tích hợp với PayOS thông qua API và xử lý các webhook để cập nhật trạng thái đơn hàng.

## 6. Quản lý mô hình AI

- **Phương pháp lưu trữ: Hệ thống tệp cục bộ**
  - **Lý do:** Các mô hình AI được lưu trữ trực tiếp trên hệ thống tệp của server. Metadata của mô hình (tên, phiên bản, đường dẫn) được lưu trữ trong cơ sở dữ liệu PostgreSQL. Điều này cho phép quản lý tập trung và truy xuất dễ dàng các mô hình.

## 7. Công cụ phát triển (Development Tooling)

- **Quản lý môi trường và gói: uv**
  - **Lý do:** `uv` là một công cụ cài đặt và phân giải gói Python cực kỳ nhanh, được phát triển bởi Astral (cùng công ty với Ruff). Nó được dùng để thay thế cho `pip` và `venv` truyền thống. Việc sử dụng `uv` giúp tăng tốc đáng kể quá trình cài đặt thư viện và quản lý môi trường ảo, cải thiện trải nghiệm của lập trình viên.

- **Linting và Formatting: Ruff**
  - **Lý do:** `Ruff` là một linter và code formatter siêu nhanh cho Python, được viết bằng Rust. Nó có thể thay thế cho nhiều công cụ khác nhau (như Flake8, isort, Black) và gộp chúng vào một công ty duy nhất. Việc tích hợp Ruff vào dự án giúp đảm bảo code luôn tuân thủ một tiêu chuẩn nhất quán, sạch sẽ và dễ đọc, đồng thời kiểm tra lỗi một cách nhanh chóng.
