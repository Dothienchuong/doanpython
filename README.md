# Ứng dụng quản lý ký túc xá (Python + Tkinter)

## Cấu trúc thư mục

ky_tuc_xa/
├── main.py            # File chạy chương trình
├── gui.py             # Giao diện Tkinter (Treeview, Canvas, DateEntry, RoomCard)
├── services.py        # Nghiệp vụ: phòng, xếp phòng, hợp đồng, hóa đơn, phân quyền, thống kê
├── models.py          # Các lớp dữ liệu (Phong, SinhVien, HopDong, HoaDon, ViPham)
├── storage.py         # Đọc/ghi JSON và CSV
├── test_services.py   # Kiểm thử đơn vị
├── requirements.txt
└── data/
    ├── du_lieu.json       # Tạo ra khi bấm Lưu (lần đầu chạy sẽ dùng dữ liệu mẫu)
    ├── sinh_vien_mau.csv  # File CSV mẫu để nhập sinh viên
    └── tai_khoan.json     # Tài khoản và mật khẩu đã băm


## Cách chạy trong VS Code

1. Cài Python 3.10 trở lên.
2. Mở thư mục `ky_tuc_xa` bằng VS Code (File → Open Folder).
3. Cài các thư viện giao diện: `pip install -r requirements.txt`
4. Chọn interpreter Python (Ctrl+Shift+P → "Python: Select Interpreter").
5. Mở `main.py` và bấm Run (F5 hoặc nút ▶).

Chạy kiểm thử: `python -m unittest test_services -v`

## Chức năng

- **Phòng**: thêm, xóa phòng; kiểm soát sức chứa; nhấp đúp để mở thẻ phòng (RoomCard).
- **Sinh viên**: thêm, sửa, xóa; xếp vào phòng, chuyển phòng, trả phòng; nhập từ CSV, xuất CSV.
- **Tìm kiếm sinh viên**: lọc kết hợp theo mã sinh viên, họ tên và phòng.
- **Sơ đồ tòa nhà**: Canvas vẽ sơ đồ theo tầng, màu theo trạng thái phòng.
- **Hợp đồng & vi phạm**: thêm, sửa hợp đồng; ghi và xóa vi phạm, cảnh báo hợp đồng sắp hết hạn (30 ngày) bằng màu vàng.
- **Điện nước & công nợ**: nhập số điện, nước theo tháng, tự tính tiền phòng + điện + nước, chia đều cho sinh viên trong phòng; đánh dấu đã thu; xuất hóa đơn CSV.
- **Thống kê**: số chỗ trống, phòng trống, phòng đầy, công nợ...
- **Đăng nhập, đăng ký và đăng xuất**: tài khoản được lưu riêng trong
  `data/tai_khoan.json`; mật khẩu không được lưu dạng rõ. Có thể đăng ký tài khoản
  sinh viên hoặc đổi mật khẩu từ màn hình đăng nhập và đăng xuất từ menu **Tệp**.
  Vai trò `nhan_vien` (Nhân viên) có thể thêm và xem dữ liệu; không được sửa,
  xóa, xếp/trả phòng hoặc đánh dấu đã thu. Các nút thao tác không được phép
  sẽ bị vô hiệu hóa trên giao diện và nghiệp vụ vẫn kiểm tra quyền ở backend.

## Đơn giá mặc định

Chỉnh trong `services.py` hoặc trong file `data/du_lieu.json`: `gia_dien` (3.500 đ/kWh), `gia_nuoc` (15.000 đ/m³). Giá phòng nhập khi tạo từng phòng.
