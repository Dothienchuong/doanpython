"""Chạy ứng dụng: python main.py"""
from gui import ManHinhDangNhap, UngDungKyTucXa

if __name__ == "__main__":
    while True:
        dang_nhap = ManHinhDangNhap()
        dang_nhap.mainloop()
        if not dang_nhap.vai_tro:
            break
        ung_dung = UngDungKyTucXa(dang_nhap.vai_tro, dang_nhap.ten_dang_nhap)
        ung_dung.mainloop()
        if not ung_dung.dang_xuat:
            break
