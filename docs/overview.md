# Tổng quan hệ thống Backend Giỏ hàng thông minh

## 1. Mục tiêu

Backend của hệ thống Giỏ hàng thông minh được thiết kế để cung cấp nền tảng vững chắc và linh hoạt, hỗ trợ trải nghiệm mua sắm hiện đại, tự động cho người dùng. Nó đóng vai trò trung tâm trong việc quản lý dữ liệu, xử lý logic nghiệp vụ phức tạp và đảm bảo đồng bộ hóa giữa các thành phần khác của hệ thống (ứng dụng di động, xe đẩy thông minh).

---

## 2. Thành phần chính

### 2.1. Server Backend (Dự án này)

Đây là trái tim của hệ thống, chịu trách nhiệm:

* **Quản lý người dùng và xác thực:** Đăng ký, đăng nhập, quản lý phiên người dùng.
* **Quản lý phiên mua sắm:** Tạo, quản lý và đồng bộ hóa giỏ hàng theo thời gian thực giữa ứng dụng di động và xe đẩy thông minh thông qua các API chuyên biệt.
* **Quản lý sản phẩm:** Lưu trữ thông tin chi tiết sản phẩm, hình ảnh, danh mục, đánh giá.
* **Quản lý yêu thích:** Cho phép người dùng lưu trữ các sản phẩm yêu thích.
* **Quản lý khuyến mãi:** Tạo và áp dụng các chương trình khuyến mãi cho sản phẩm và danh mục.
* **Quản lý đơn hàng:** Xử lý quy trình tạo đơn hàng, theo dõi trạng thái và lịch sử mua sắm.
* **Tích hợp thanh toán:** Lắng nghe và xử lý các webhook từ cổng thanh toán (ví dụ: PayOS) để xác nhận và hoàn tất đơn hàng.
* **Hệ thống thông báo:** Gửi thông báo tự động đến người dùng về trạng thái đơn hàng, khuyến mãi, v.v.
* **Quản lý mô hình AI:** Cung cấp API để tải lên, tải xuống, liệt kê và xóa các mô hình AI được sử dụng bởi các thành phần khác của hệ thống (ví dụ: cho nhận diện sản phẩm).

### 2.2. Ứng dụng di động (Client)

Ứng dụng di động tương tác với Backend để:

* Đăng nhập/đăng ký người dùng.
* Quét mã QR trên xe đẩy để liên kết phiên mua sắm.
* Hiển thị giỏ hàng theo thời gian thực.
* Thực hiện thanh toán online.

### 2.3. Xe đẩy thông minh (Client)

Xe đẩy thông minh kết nối với Backend để:

* Đồng bộ trạng thái giỏ hàng.
* Gửi dữ liệu nhận diện sản phẩm (nếu xử lý trên xe đẩy).
* Nhận thông tin phiên mua sắm và người dùng.

---

## 3. Quy trình hoạt động (Vai trò của Backend)

1. **Xác thực phiên:** Người dùng đăng nhập vào Ứng dụng di động, quét mã QR trên xe đẩy. Backend xác thực mã QR, liên kết người dùng với xe đẩy và tạo/kích hoạt một phiên mua sắm.
2. **Cập nhật giỏ hàng:** Khi sản phẩm được thêm/bớt vào xe đẩy, xe đẩy gửi yêu cầu cập nhật đến Backend. Backend xử lý logic thêm/bớt/cập nhật số lượng sản phẩm trong phiên mua sắm và đồng bộ trạng thái này với Ứng dụng di động.
3. **Thanh toán:** Người dùng khởi tạo thanh toán qua Ứng dụng di động. Backend tạo yêu cầu thanh toán với cổng thanh toán và lắng nghe webhook phản hồi trạng thái giao dịch.
4. **Hoàn tất đơn hàng & Thông báo:** Khi Backend nhận được xác nhận thanh toán thành công từ webhook, nó sẽ hoàn tất đơn hàng, chuyển các mặt hàng từ phiên mua sắm sang đơn hàng và gửi thông báo xác nhận đến người dùng.
5. **Quản lý dữ liệu:** Backend quản lý tất cả dữ liệu về người dùng, sản phẩm, khuyến mãi, đơn hàng và mô hình AI, cung cấp các API cho việc truy xuất và thao tác dữ liệu.

---

## 4. Điểm nổi bật của Backend

* **Đồng bộ hóa dữ liệu mạnh mẽ:** Đảm bảo giỏ hàng và trạng thái phiên mua sắm được đồng bộ hóa theo thời gian thực giữa các thiết bị.
* **API linh hoạt:** Cung cấp các API rõ ràng, dễ sử dụng cho các ứng dụng client và xe đẩy thông minh.
* **Tích hợp thanh toán an toàn:** Xử lý webhook thanh toán một cách bảo mật và đáng tin cậy.
* **Quản lý tài nguyên tập trung:** Quản lý tập trung thông tin sản phẩm, người dùng, đơn hàng và các mô hình AI.
* **Khả năng mở rộng:** Được xây dựng trên FastAPI và SQLModel, cho phép mở rộng dễ dàng các tính năng trong tương lai.
