"""Giao diện Tkinter cho ứng dụng quản lý ký túc xá."""
import functools
import os
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk, messagebox, filedialog

import storage
from models import Phong, SinhVien, HopDong, HoaDon, ViPham
from services import (QUYEN, DormService, dang_ky_tai_khoan, ma_sv_cua_tai_khoan,
                      doi_mat_khau, tao_du_lieu_mau, xac_thuc)

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

FILE_DU_LIEU = storage.DUONG_DAN_MAC_DINH
MAU_TRONG = "#c8f7c5"   
MAU_SAP_DAY = "#ffe9a8"  
MAU_DAY = "#f7c5c5"      
FONT_TIEU_DE = ("Segoe UI", 12, "bold")
MAU_NEN = "#f4f7fb"
MAU_THE = "#ffffff"
MAU_CHU = "#243447"
MAU_PHU = "#68788a"
MAU_XANH = "#2563eb"
MAU_XANH_DAM = "#1d4ed8"


# ---------- Hàm tiện ích ----------
def xu_ly_loi(ham):
    """Bắt lỗi nghiệp vụ và hiển thị hộp thoại thay vì làm sập chương trình."""
    @functools.wraps(ham)
    def boc(self, *args, **kwargs):
        try:
            return ham(self, *args, **kwargs)
        except (ValueError, PermissionError) as e:
            messagebox.showerror("Thông báo", str(e), parent=self)
    return boc


def tao_o_ngay(cha):
    if DateEntry:
        return DateEntry(cha, date_pattern="yyyy-mm-dd", width=12)
    o = ttk.Entry(cha, width=14)
    o.insert(0, date.today().isoformat())
    return o


def lay_ngay(o):
    if DateEntry and isinstance(o, DateEntry):
        return o.get_date().isoformat()
    try:
        return date.fromisoformat(o.get().strip()).isoformat()
    except ValueError:
        raise ValueError("Ngày phải có dạng YYYY-MM-DD, ví dụ 2026-10-17.")


def dat_ngay(o, gia_tri):
    if DateEntry and isinstance(o, DateEntry):
        o.set_date(date.fromisoformat(gia_tri))
    else:
        o.delete(0, "end")
        o.insert(0, gia_tri)


def lay_so(o, ten, kieu=float):
    try:
        return kieu(o.get().strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"'{ten}' phải là số hợp lệ.")


def _chon(tree):
    s = tree.selection()
    return s[0] if s else ""


# ---------- Thẻ phòng tùy biến (Custom RoomCard) ----------
class TheCanPhong(tk.Toplevel):
    def __init__(self, cha, svc, p):
        super().__init__(cha)
        self.title(f"Thẻ phòng {p.ma_phong}")
        self.resizable(False, False)
        self.configure(bg=MAU_NEN)
        if p.so_cho_trong == 0:
            mau, trang_thai = MAU_DAY, "ĐÃ ĐẦY"
        elif not p.ma_sv:
            mau, trang_thai = MAU_TRONG, "TRỐNG"
        else:
            mau, trang_thai = MAU_SAP_DAY, f"CÒN {p.so_cho_trong} CHỖ"

        dau = tk.Frame(self, bg=mau, padx=14, pady=10)
        dau.pack(fill="x")
        tk.Label(dau, text=f"Phòng {p.ma_phong}", font=FONT_TIEU_DE, bg=mau).pack(anchor="w")
        tk.Label(dau, text=f"Tòa {p.toa_nha} • Tầng {p.tang} • {trang_thai}", bg=mau).pack(anchor="w")

        than = ttk.Frame(self, padding=14)
        than.pack(fill="both")
        ttk.Label(than, text=f"Giá thuê: {p.gia_thue:,.0f} đ/tháng").pack(anchor="w")
        ttk.Label(than, text=f"Sức chứa: {p.suc_chua} chỗ").pack(anchor="w")
        ttk.Label(than, text="Sinh viên đang ở:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 2))
        ds = [f"• {svc.sinh_vien[m].ma_sv} - {svc.sinh_vien[m].ho_ten}" for m in p.ma_sv]
        ttk.Label(than, text="\n".join(ds) or "(chưa có sinh viên)", justify="left").pack(anchor="w")
        ttk.Button(than, text="Đóng", command=self.destroy).pack(anchor="e", pady=(12, 0))


# ---------- Đăng nhập ----------
# Bảng màu riêng cho màn hình đăng nhập: xanh biển & trắng
DN_XANH = "#1559d6"
DN_XANH_HOVER = "#0f47b3"
DN_XANH_NHAN = "#0b3a8f"
DN_XANH_NHAT = "#eaf1fd"
DN_XANH_NHAT_HOVER = "#d7e5fb"
DN_NAVY_TREN = "#071b4d"
DN_NAVY_DUOI = "#1a63d9"
DN_VIEN = "#d3deef"
DN_CHU = "#0f2347"
DN_CHU_PHU = "#6b7c93"
DN_CHU_NHAT = "#c9dafc"
DN_LOI = "#d92d20"
DN_FONT = "Segoe UI"


def _pha_mau(mau1, mau2, t):
    """Trộn hai màu dạng #rrggbb theo tỉ lệ t (0 = mau1, 1 = mau2)."""
    a = [int(mau1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(mau2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _ve_hinh_bo_goc(canvas, x1, y1, x2, y2, r, **kieu):
    """Vẽ hình chữ nhật bo góc trên Canvas."""
    diem = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(diem, smooth=True, **kieu)


def _can_giua_cua_so(cua_so, rong=None, cao=None, cha=None):
    """Đặt cửa sổ vào giữa màn hình (hoặc giữa cửa sổ cha)."""
    cua_so.update_idletasks()
    rong = rong or cua_so.winfo_reqwidth()
    cao = cao or cua_so.winfo_reqheight()
    if cha is not None and cha.winfo_viewable():
        x = cha.winfo_rootx() + (cha.winfo_width() - rong) // 2
        y = cha.winfo_rooty() + (cha.winfo_height() - cao) // 2
    else:
        x = (cua_so.winfo_screenwidth() - rong) // 2
        y = (cua_so.winfo_screenheight() - cao) // 2 - 20
    cua_so.geometry(f"{rong}x{cao}+{max(x, 0)}+{max(y, 0)}")


class BenTraiDangNhap(tk.Canvas):
    """Khung thương hiệu bên trái: nền xanh biển chuyển sắc, logo và điểm nổi bật."""

    def __init__(self, cha, rong, cao):
        super().__init__(cha, width=rong, height=cao, highlightthickness=0, bd=0)
        self.rong_nen = rong
        self.cao_nen = cao
        self._ve()

    def _mau(self, y):
        t = min(max(y, 0), self.cao_nen - 1) / (self.cao_nen - 1)
        return _pha_mau(DN_NAVY_TREN, DN_NAVY_DUOI, t)

    def _ve(self):
        r, c = self.rong_nen, self.cao_nen
        # Nền chuyển sắc từ xanh navy sang xanh biển
        for y in range(c):
            self.create_line(0, y, r, y, fill=self._mau(y))
        # Các vòng tròn trang trí
        self.create_oval(-110, -110, 150, 150,
                         fill=_pha_mau(self._mau(20), "#ffffff", 0.06), outline="")
        for ban_kinh in (130, 210, 290, 370):
            mau = _pha_mau(self._mau(c - ban_kinh), "#ffffff", 0.13)
            self.create_oval(r - ban_kinh, c - ban_kinh, r + ban_kinh, c + ban_kinh,
                             outline=mau, width=1)

        # Logo: ô vuông trắng bo góc + toà nhà
        _ve_hinh_bo_goc(self, 44, 52, 96, 104, 14, fill="white", outline="")
        self.create_rectangle(56, 62, 84, 94, fill=DN_XANH, outline="")
        for x in (61, 73):
            for y in (66, 75):
                self.create_rectangle(x, y, x + 6, y + 5, fill="white", outline="")
        self.create_rectangle(67, 84, 73, 94, fill="white", outline="")
        self.create_text(112, 66, text="KÝ TÚC XÁ", fill="white", anchor="w",
                         font=(DN_FONT, 15, "bold"))
        self.create_text(112, 90, text="Hệ thống quản lý", fill=DN_CHU_NHAT, anchor="w",
                         font=(DN_FONT, 10))

        # Thông điệp chính
        self.create_text(44, 188, text="Quản lý ký túc xá\nđơn giản, hiện đại",
                         fill="white", anchor="nw", justify="left",
                         font=(DN_FONT, 19, "bold"))
        self.create_text(44, 276, width=292, anchor="nw", fill=DN_CHU_NHAT,
                         font=(DN_FONT, 10),
                         text="Theo dõi phòng ở, sinh viên, hợp đồng và công nợ "
                              "trên một nền tảng duy nhất.")

        # Điểm nổi bật
        diem_noi_bat = ("Quản lý phòng & sinh viên",
                        "Hợp đồng, vi phạm & hóa đơn",
                        "Thống kê trực quan")
        for i, noi_dung in enumerate(diem_noi_bat):
            y = 406 + i * 38
            self.create_oval(44, y - 11, 66, y + 11, fill="white", outline="")
            self.create_line(50, y, 54, y + 4, 61, y - 4, fill=DN_XANH, width=2)
            self.create_text(80, y, text=noi_dung, fill="white", anchor="w",
                             font=(DN_FONT, 10))

        self.create_text(44, c - 30, text="© 2026 Quản lý Ký túc xá", anchor="w",
                         fill=_pha_mau(DN_NAVY_DUOI, "#ffffff", 0.55),
                         font=(DN_FONT, 8))


class NutBam(tk.Canvas):
    """Nút bấm bo góc, đổi màu khi rê chuột / nhấn."""

    def __init__(self, cha, text, command, cao=48, nen="white"):
        super().__init__(cha, height=cao, bg=nen, highlightthickness=0, bd=0,
                         cursor="hand2")
        self._chu = text
        self._lenh = command
        self._mau_nut = DN_XANH
        self.bind("<Configure>", lambda _e: self._ve())
        self.bind("<Enter>", lambda _e: self._doi_mau(DN_XANH_HOVER))
        self.bind("<Leave>", lambda _e: self._doi_mau(DN_XANH))
        self.bind("<ButtonPress-1>", lambda _e: self._doi_mau(DN_XANH_NHAN))
        self.bind("<ButtonRelease-1>", self._nha_chuot)

    def _ve(self):
        self.delete("all")
        r, c = self.winfo_width(), self.winfo_height()
        _ve_hinh_bo_goc(self, 1, 1, r - 1, c - 1, 12,
                        fill=self._mau_nut, outline=self._mau_nut)
        self.create_text(r // 2, c // 2, text=self._chu, fill="white",
                         font=(DN_FONT, 11, "bold"))

    def _doi_mau(self, mau):
        self._mau_nut = mau
        self._ve()

    def _nha_chuot(self, e):
        ben_trong = 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height()
        self._doi_mau(DN_XANH_HOVER if ben_trong else DN_XANH)
        if ben_trong:
            self._lenh()


class OGachChan(tk.Frame):
    """Ô nhập kiểu gạch chân: nhãn nhỏ phía trên, đường kẻ đổi sang xanh khi đang nhập."""

    def __init__(self, cha, nhan, an=False, nen="white"):
        super().__init__(cha, bg=nen)
        tk.Label(self, text=nhan.upper(), bg=nen, fg=DN_CHU_PHU,
                 font=(DN_FONT, 8, "bold")).pack(anchor="w")
        hang = tk.Frame(self, bg=nen)
        hang.pack(fill="x", pady=(4, 0))
        self.entry = tk.Entry(hang, bd=0, relief="flat", highlightthickness=0,
                              bg=nen, fg=DN_CHU, insertbackground=DN_XANH,
                              font=(DN_FONT, 12), show="•" if an else "")
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.nut_hien = None
        if an:
            self.nut_hien = tk.Label(hang, text="HIỆN", bg=nen, fg=DN_XANH,
                                     font=(DN_FONT, 8, "bold"), cursor="hand2")
            self.nut_hien.pack(side="right", padx=(8, 0))
            self.nut_hien.bind("<Button-1>", self._chuyen_hien_an)
        self.gach = tk.Frame(self, height=2, bg=DN_VIEN)
        self.gach.pack(fill="x", pady=(2, 0))
        self.entry.bind("<FocusIn>", lambda _e: self.gach.configure(bg=DN_XANH))
        self.entry.bind("<FocusOut>", lambda _e: self.gach.configure(bg=DN_VIEN))

    def _chuyen_hien_an(self, _e=None):
        dang_an = self.entry.cget("show") != ""
        self.entry.configure(show="" if dang_an else "•")
        self.nut_hien.configure(text="ẨN" if dang_an else "HIỆN")

    def get(self):
        return self.entry.get()

    def xoa(self):
        self.entry.delete(0, "end")

    def chen(self, noi_dung):
        self.entry.insert(0, noi_dung)

    def focus_set(self):
        self.entry.focus_set()


class ChonVaiTro(tk.Frame):
    """Bộ chọn loại tài khoản dạng thanh phân đoạn (segmented control)."""

    def __init__(self, cha, cac_muc, bien, khi_doi=None):
        super().__init__(cha, bg=DN_XANH_NHAT, padx=4, pady=4)
        self._bien = bien
        self._khi_doi = khi_doi
        self._nut = {}
        for cot, (gia_tri, nhan) in enumerate(cac_muc):
            lb = tk.Label(self, text=nhan, font=(DN_FONT, 10, "bold"),
                          cursor="hand2", pady=8)
            lb.grid(row=0, column=cot, sticky="nsew", padx=1)
            self.columnconfigure(cot, weight=1, uniform="vai_tro")
            lb.bind("<Button-1>", lambda _e, g=gia_tri: self.chon(g))
            lb.bind("<Enter>", lambda _e, g=gia_tri: self._ve(g))
            lb.bind("<Leave>", lambda _e: self._ve())
            self._nut[gia_tri] = lb
        self._ve()

    def chon(self, gia_tri):
        self._bien.set(gia_tri)
        self._ve()
        if self._khi_doi:
            self._khi_doi()

    def _ve(self, dang_tro=None):
        da_chon = self._bien.get()
        for gia_tri, lb in self._nut.items():
            if gia_tri == da_chon:
                lb.configure(bg=DN_XANH, fg="white")
            elif gia_tri == dang_tro:
                lb.configure(bg=DN_XANH_NHAT_HOVER, fg=DN_XANH)
            else:
                lb.configure(bg=DN_XANH_NHAT, fg="#3d5a8c")


def _tao_lien_ket(cha, text, command, nen="white", co_chu=10):
    """Nhãn dạng liên kết: chữ xanh, gạch chân khi rê chuột."""
    lb = tk.Label(cha, text=text, bg=nen, fg=DN_XANH, cursor="hand2",
                  font=(DN_FONT, co_chu, "bold"))
    lb.bind("<Button-1>", lambda _e: command())
    lb.bind("<Enter>", lambda _e: lb.configure(font=(DN_FONT, co_chu, "bold underline")))
    lb.bind("<Leave>", lambda _e: lb.configure(font=(DN_FONT, co_chu, "bold")))
    return lb


class ManHinhDangNhap(tk.Tk):
    RONG, CAO, TRAI = 920, 580, 380

    def __init__(self):
        super().__init__()
        self.vai_tro = None
        self.ten_dang_nhap = None
        self.title("Đăng nhập - Quản lý Ký túc xá")
        self.resizable(False, False)
        self.configure(bg="white")
        self._tao_giao_dien()
        _can_giua_cua_so(self, self.RONG, self.CAO)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.o_ten.focus_set()
        self._hien_dan()

    def _hien_dan(self, do_dac=0.0):
        """Hiệu ứng mờ dần khi mở cửa sổ (bỏ qua nếu hệ thống không hỗ trợ)."""
        try:
            self.attributes("-alpha", min(do_dac, 1.0))
        except tk.TclError:
            return
        if do_dac < 1.0:
            self.after(15, lambda: self._hien_dan(do_dac + 0.12))

    def _tao_giao_dien(self):
        BenTraiDangNhap(self, self.TRAI, self.CAO).pack(side="left", fill="y")
        phai = tk.Frame(self, bg="white")
        phai.pack(side="right", fill="both", expand=True)
        nd = tk.Frame(phai, bg="white")
        nd.pack(fill="both", expand=True, padx=64, pady=(50, 24))

        tk.Label(nd, text="ĐĂNG NHẬP HỆ THỐNG", bg="white", fg=DN_XANH,
                 font=(DN_FONT, 9, "bold")).pack(anchor="w")
        tk.Label(nd, text="Chào mừng trở lại", bg="white", fg=DN_CHU,
                 font=(DN_FONT, 24, "bold")).pack(anchor="w", pady=(4, 0))
        self.lbl_vai_tro = tk.Label(nd, text="", bg="white", fg=DN_CHU_PHU,
                                    font=(DN_FONT, 10), anchor="w", justify="left")
        self.lbl_vai_tro.pack(anchor="w", pady=(6, 0))

        self.vai_tro_chon = tk.StringVar(value="admin")
        self.chon_vai_tro = ChonVaiTro(
            nd, (("admin", "Quản trị viên"), ("nhan_vien", "Nhân viên"),
                 ("sinh_vien", "Sinh viên")),
            self.vai_tro_chon, self._cap_nhat_tieu_de)
        self.chon_vai_tro.pack(fill="x", pady=(22, 0))

        self.o_ten = OGachChan(nd, "Tên đăng nhập")
        self.o_ten.pack(fill="x", pady=(26, 0))
        self.o_mat_khau = OGachChan(nd, "Mật khẩu", an=True)
        self.o_mat_khau.pack(fill="x", pady=(20, 0))
        self.o_ten.entry.bind("<Return>", lambda _e: self.o_mat_khau.focus_set())
        self.o_mat_khau.entry.bind("<Return>", lambda _e: self._dang_nhap())
        for o in (self.o_ten, self.o_mat_khau):
            o.entry.bind("<Key>", lambda _e: self.lbl_loi.configure(text=""))

        self.lbl_loi = tk.Label(nd, text="", bg="white", fg=DN_LOI, height=1,
                                font=(DN_FONT, 9), anchor="w", justify="left",
                                wraplength=412)
        self.lbl_loi.pack(fill="x", pady=(10, 0))
        NutBam(nd, "ĐĂNG NHẬP", self._dang_nhap).pack(fill="x", pady=(8, 0))

        hang = tk.Frame(nd, bg="white")
        hang.pack(pady=(20, 0))
        tk.Label(hang, text="Chưa có tài khoản sinh viên?", bg="white",
                 fg=DN_CHU_PHU, font=(DN_FONT, 10)).pack(side="left")
        _tao_lien_ket(hang, "Đăng ký ngay", self._dang_ky).pack(side="left", padx=(6, 0))
        _tao_lien_ket(nd, "Đổi mật khẩu", self._doi_mat_khau, co_chu=9).pack(
            anchor="e", pady=(14, 0))
        self._cap_nhat_tieu_de()

    def _cap_nhat_tieu_de(self):
        nhan = {"admin": "quản trị viên", "nhan_vien": "nhân viên",
                "sinh_vien": "sinh viên"}
        self.lbl_vai_tro.configure(
            text=f"Đăng nhập với tư cách {nhan[self.vai_tro_chon.get()]}")
        self.lbl_loi.configure(text="")

    def _dang_nhap(self):
        vai_tro = self.vai_tro_chon.get()
        ten = self.o_ten.get().strip()
        mat_khau = self.o_mat_khau.get()
        if not ten or not mat_khau:
            self.lbl_loi.configure(text="Vui lòng nhập tên đăng nhập và mật khẩu.")
            return
        if xac_thuc(ten, mat_khau, vai_tro):
            self.vai_tro = vai_tro
            self.ten_dang_nhap = ten
            self.destroy()
            return
        self.lbl_loi.configure(text="Tên đăng nhập hoặc mật khẩu không đúng.")
        self.o_mat_khau.xoa()
        self.o_mat_khau.focus_set()

    def _doi_mat_khau(self):
        """Mở biểu mẫu đổi mật khẩu cho tài khoản và vai trò đang chọn."""
        hop = tk.Toplevel(self)
        hop.title("Đổi mật khẩu")
        hop.configure(bg="white")
        hop.resizable(False, False)
        hop.transient(self)

        than = tk.Frame(hop, bg="white")
        than.pack(fill="both", expand=True, padx=36, pady=24)
        o_ten = OGachChan(than, "Tên đăng nhập")
        o_ten.pack(fill="x", pady=(0, 14))
        o_ten.chen(self.o_ten.get().strip())
        o_cu = OGachChan(than, "Mật khẩu hiện tại", an=True)
        o_cu.pack(fill="x", pady=(0, 14))
        o_moi = OGachChan(than, "Mật khẩu mới", an=True)
        o_moi.pack(fill="x", pady=(0, 14))
        o_xn = OGachChan(than, "Nhập lại mật khẩu mới", an=True)
        o_xn.pack(fill="x", pady=(0, 8))
        lbl_loi = tk.Label(than, text="", bg="white", fg=DN_LOI,
                           font=(DN_FONT, 9), anchor="w", justify="left",
                           wraplength=368)
        lbl_loi.pack(fill="x", pady=(4, 8))

        def luu_mat_khau():
            ten = o_ten.get().strip()
            if o_moi.get() != o_xn.get():
                lbl_loi.configure(text="Mật khẩu mới nhập lại không khớp.")
                return
            try:
                doi_mat_khau(ten, self.vai_tro_chon.get(), o_cu.get(), o_moi.get())
            except ValueError as loi:
                lbl_loi.configure(text=str(loi))
                return
            messagebox.showinfo("Đổi mật khẩu", "Đổi mật khẩu thành công.", parent=hop)
            hop.destroy()

        NutBam(than, "LƯU MẬT KHẨU", luu_mat_khau).pack(fill="x")
        _tao_lien_ket(than, "← Quay lại đăng nhập", hop.destroy, co_chu=9).pack(pady=(14, 0))
        o_xn.entry.bind("<Return>", lambda _e: luu_mat_khau())
        hop.bind("<Escape>", lambda _e: hop.destroy())
        _can_giua_cua_so(hop, 440, None, self)
        try:
            hop.grab_set()
        except tk.TclError:
            pass
        o_cu.focus_set()

    def _dang_ky(self):
        hop = tk.Toplevel(self)
        hop.title("Đăng ký tài khoản")
        hop.configure(bg="white")
        hop.resizable(False, False)
        hop.transient(self)

        dau = tk.Frame(hop, bg=DN_XANH)
        dau.pack(fill="x")
        tk.Label(dau, text="Tạo tài khoản sinh viên", bg=DN_XANH, fg="white",
                 font=(DN_FONT, 16, "bold")).pack(anchor="w", padx=36, pady=(26, 2))
        tk.Label(dau, text="Nhập đúng mã sinh viên để xem thông tin phòng của bạn.",
                 bg=DN_XANH, fg=DN_CHU_NHAT, font=(DN_FONT, 10)).pack(
            anchor="w", padx=36, pady=(0, 24))

        than = tk.Frame(hop, bg="white")
        than.pack(fill="both", expand=True, padx=36, pady=(6, 24))
        o_ma = OGachChan(than, "Mã sinh viên")
        o_ma.pack(fill="x", pady=(18, 0))
        o_ten = OGachChan(than, "Tên đăng nhập")
        o_ten.pack(fill="x", pady=(18, 0))
        o_mk = OGachChan(than, "Mật khẩu", an=True)
        o_mk.pack(fill="x", pady=(18, 0))
        o_xn = OGachChan(than, "Nhập lại mật khẩu", an=True)
        o_xn.pack(fill="x", pady=(18, 0))
        lbl_loi = tk.Label(than, text="", bg="white", fg=DN_LOI, height=1,
                           font=(DN_FONT, 9), anchor="w", justify="left", wraplength=368)
        lbl_loi.pack(fill="x", pady=(10, 0))

        def luu_tai_khoan():
            ten = o_ten.get().strip()
            if o_mk.get() != o_xn.get():
                lbl_loi.configure(text="Mật khẩu nhập lại không khớp.")
                return
            try:
                dang_ky_tai_khoan(ten, o_mk.get(), ma_sv=o_ma.get())
            except ValueError as loi:
                lbl_loi.configure(text=str(loi))
                return
            messagebox.showinfo("Đăng ký", "Đăng ký tài khoản thành công.", parent=hop)
            self.o_ten.xoa()
            self.o_ten.chen(ten)
            self.o_mat_khau.xoa()
            self.chon_vai_tro.chon("sinh_vien")
            hop.destroy()
            self.o_mat_khau.focus_set()

        NutBam(than, "TẠO TÀI KHOẢN", luu_tai_khoan).pack(fill="x", pady=(8, 0))
        _tao_lien_ket(than, "← Quay lại đăng nhập", hop.destroy, co_chu=9).pack(pady=(16, 0))

        o_ma.entry.bind("<Return>", lambda _e: o_ten.focus_set())
        o_ten.entry.bind("<Return>", lambda _e: o_mk.focus_set())
        o_mk.entry.bind("<Return>", lambda _e: o_xn.focus_set())
        o_xn.entry.bind("<Return>", lambda _e: luu_tai_khoan())
        for o in (o_ma, o_ten, o_mk, o_xn):
            o.entry.bind("<Key>", lambda _e: lbl_loi.configure(text=""))
        hop.bind("<Escape>", lambda _e: hop.destroy())

        _can_giua_cua_so(hop, 440, None, self)
        try:
            hop.grab_set()
        except tk.TclError:
            pass
        o_ma.focus_set()


# ---------- Cửa sổ chính ----------
class UngDungKyTucXa(tk.Tk):
    def __init__(self, vai_tro="admin", ten_dang_nhap=""):
        super().__init__()
        self.dang_xuat = False
        self.ten_dang_nhap = ten_dang_nhap
        self.la_sinh_vien = vai_tro == "sinh_vien"
        self.ma_sv = ""
        self.ma_phong_cua_toi = ""
        self.title("Quản lý Ký túc xá" + (" - Sinh viên" if self.la_sinh_vien else ""))
        self.geometry("1250x780")
        self.minsize(1000, 650)
        self._cau_hinh_giao_dien()

        if os.path.exists(FILE_DU_LIEU):
            self.svc = DormService.from_dict(storage.doc_json(FILE_DU_LIEU), vai_tro)
        else:
            self.svc = tao_du_lieu_mau(DormService("admin"))
            self.svc.vai_tro = vai_tro
        self.svc_quyen = QUYEN.get(self.svc.vai_tro, set())
        if self.la_sinh_vien:
            self.ma_sv = self._tim_ma_sv()

        self._tao_menu()
        self._tao_tieu_de()
        self._tao_thanh_vai_tro()
        self.so = ttk.Notebook(self)
        self.so.pack(fill="both", expand=True, padx=18, pady=(8, 12))
        self.trang_thai = tk.StringVar(value="Sẵn sàng")
        ttk.Label(self, textvariable=self.trang_thai, style="Status.TLabel",
                  anchor="w").pack(fill="x", padx=18, pady=(0, 8))
        if self.la_sinh_vien:
            # Sinh viên chỉ xem: phòng của mình, sơ đồ, hợp đồng, điện nước & công nợ, thống kê
            self._tab_phong_cua_toi()
            self._tab_so_do()
            self._tab_hop_dong_sv()
            self._tab_hoa_don_sv()
            self._tab_thong_ke()
        else:
            self._tab_phong()
            self._tab_sinh_vien()
            self._tab_so_do()
            self._tab_hop_dong()
            self._tab_hoa_don()
            self._tab_thong_ke()
        self.protocol("WM_DELETE_WINDOW", self._thoat)
        self.lam_moi_tat_ca()

    # ----- Menu & thanh vai trò -----
    def _cau_hinh_giao_dien(self):
        self.configure(bg=MAU_NEN)
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("Segoe UI", 10), foreground=MAU_CHU)
        style.configure("TFrame", background=MAU_NEN)
        style.configure("TLabel", background=MAU_NEN, foreground=MAU_CHU)
        style.configure("TButton", padding=(12, 7), font=("Segoe UI", 10, "bold"))
        style.map("TButton", foreground=[("active", "white")],
                  background=[("active", MAU_XANH_DAM)])
        style.configure("Primary.TButton", background=MAU_XANH, foreground="white")
        style.map("Primary.TButton", background=[("active", MAU_XANH_DAM)])
        style.configure("TLabelframe", background=MAU_NEN, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=MAU_NEN, foreground=MAU_XANH,
                        font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook", background=MAU_NEN, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 9), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", foreground=[("selected", MAU_XANH)])
        style.configure("Treeview", background=MAU_THE, fieldbackground=MAU_THE,
                        foreground=MAU_CHU, rowheight=30, borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#e8eef7", foreground=MAU_CHU,
                        font=("Segoe UI", 10, "bold"), padding=(8, 8))
        style.map("Treeview", background=[("selected", "#dbeafe")],
                  foreground=[("selected", MAU_CHU)])
        style.configure("Status.TLabel", background="#e8eef7", foreground=MAU_PHU,
                        padding=(10, 7), font=("Segoe UI", 9))

    def _tao_tieu_de(self):
        dau = tk.Frame(self, bg=MAU_XANH, padx=22, pady=16)
        dau.pack(fill="x")
        trai = tk.Frame(dau, bg=MAU_XANH)
        trai.pack(side="left")
        tk.Label(trai, text="QUẢN LÝ KÝ TÚC XÁ", bg=MAU_XANH, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(trai, text=("Thông tin phòng ở, hợp đồng và công nợ của bạn" if self.la_sinh_vien
                             else "Theo dõi phòng ở, sinh viên và công nợ tập trung"),
                 bg=MAU_XANH, fg="#dbeafe", font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))
        # Nút Đăng xuất hiện sẵn ở góc phải (vẫn có thêm trong menu Tệp)
        nut_dx = tk.Label(dau, text="Đăng xuất", bg=MAU_XANH_DAM, fg="white", cursor="hand2",
                          font=("Segoe UI", 10, "bold"), padx=18, pady=8)
        nut_dx.pack(side="right")
        nut_dx.bind("<Button-1>", lambda _e: self._dang_xuat())
        nut_dx.bind("<Enter>", lambda _e: nut_dx.configure(bg="#1e40af"))
        nut_dx.bind("<Leave>", lambda _e: nut_dx.configure(bg=MAU_XANH_DAM))
        self.lbl_tom_tat = tk.Label(dau, text="", bg=MAU_XANH, fg="white",
                                    font=("Segoe UI", 10, "bold"))
        self.lbl_tom_tat.pack(side="right", padx=(16, 16))

    def _tao_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)
        tep = tk.Menu(menu, tearoff=0)
        if not self.la_sinh_vien:
            tep.add_command(label="Lưu dữ liệu", command=self._luu)
            tep.add_command(label="Nhập sinh viên từ CSV...", command=self._nhap_csv)
            tep.add_command(label="Xuất sinh viên ra CSV...", command=self._xuat_sv_csv)
            tep.add_separator()
        tep.add_command(label="Đăng xuất", command=self._dang_xuat)
        tep.add_separator()
        tep.add_command(label="Thoát", command=self._thoat)
        menu.add_cascade(label="Tệp", menu=tep)

    def _tao_thanh_vai_tro(self):
        thanh = ttk.Frame(self, padding=(18, 10, 18, 2))
        thanh.pack(fill="x")
        ttk.Label(thanh, text="PHIÊN LÀM VIỆC", foreground=MAU_PHU,
                  font=("Segoe UI", 9, "bold")).pack(side="left")
        nhan_vai_tro = {"admin": "Quản trị viên", "nhan_vien": "Nhân viên",
                        "khach": "Khách", "sinh_vien": "Sinh viên"}
        ttk.Label(thanh, text=f"Vai trò: {nhan_vai_tro.get(self.svc.vai_tro, self.svc.vai_tro)}",
                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=(16, 4))
        if self.la_sinh_vien:
            ghi_chu = f"Tài khoản: {self.ten_dang_nhap}  •  Mã SV: {self.ma_sv or 'chưa liên kết'}  •  chỉ xem"
        else:
            ghi_chu = "admin: toàn quyền • nhân viên: chỉ thêm/xem • sinh viên: chỉ xem"
        ttk.Label(thanh, text=ghi_chu, foreground=MAU_PHU).pack(side="left", padx=10)

    def _trang_thai_quyen(self, hanh_dong):
        return "normal" if hanh_dong in self.svc_quyen else "disabled"

    # ----- Hàm dựng chung -----
    @staticmethod
    def _o(cha, nhan, cot, rong=12, widget=None, dong=0):
        ttk.Label(cha, text=nhan).grid(row=dong, column=cot * 2, sticky="w", padx=(8, 2), pady=4)
        w = widget if widget is not None else ttk.Entry(cha, width=rong)
        w.grid(row=dong, column=cot * 2 + 1, padx=(0, 8), pady=4, sticky="w")
        return w

    def _tao_bang(self, cha, cot, cao=10):
        khung = ttk.Frame(cha)
        khung.pack(fill="both", expand=True, pady=(10, 8))
        bang = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings", height=cao)
        for ma, tieu, rong in cot:
            bang.heading(ma, text=tieu)
            bang.column(ma, width=rong, anchor="w")
        cuon = ttk.Scrollbar(khung, orient="vertical", command=bang.yview)
        bang.configure(yscrollcommand=cuon.set)
        bang.pack(side="left", fill="both", expand=True)
        cuon.pack(side="right", fill="y")
        bang.tag_configure("trong", background=MAU_TRONG)
        bang.tag_configure("day", background=MAU_DAY)
        bang.tag_configure("sap", background=MAU_SAP_DAY)
        bang.tag_configure("stripe", background="#f8fafc")
        return bang

    # ----- Tab Phòng -----
    def _tab_phong(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Phòng")
        form = ttk.LabelFrame(tab, text="Thêm phòng", padding=6)
        form.pack(fill="x")
        self.e_ma = self._o(form, "Mã phòng", 0, 8)
        self.e_toa = self._o(form, "Tòa", 1, 5)
        self.e_tang = self._o(form, "Tầng", 2, 4)
        self.e_suc = self._o(form, "Sức chứa", 3, 4)
        self.e_gia = self._o(form, "Giá thuê (đ)", 4, 11)
        ttk.Button(form, text="Thêm phòng", command=self._them_phong).grid(row=0, column=10, padx=8)

        self.bang_phong = self._tao_bang(tab, [
            ("ma", "Mã phòng", 100), ("toa", "Tòa", 70), ("tang", "Tầng", 70),
            ("suc", "Sức chứa", 90), ("trong", "Còn trống", 90), ("gia", "Giá thuê (đ)", 130)])
        self.bang_phong.bind("<Double-1>", self._mo_the_phong)

        thao_tac = ttk.Frame(tab)
        thao_tac.pack(fill="x")
        ttk.Button(thao_tac, text="Xóa phòng đã chọn", command=self._xoa_phong,
                   state=self._trang_thai_quyen("xoa")).pack(side="left")
        ttk.Label(thao_tac, text="Nhấp đúp để xem thẻ phòng • Xanh: trống • Vàng: đang ở • Đỏ: đã đầy"
                  ).pack(side="left", padx=12)

    @xu_ly_loi
    def _them_phong(self):
        p = Phong(self.e_ma.get().strip(), self.e_toa.get().strip(),
                  lay_so(self.e_tang, "Tầng", int), lay_so(self.e_suc, "Sức chứa", int),
                  lay_so(self.e_gia, "Giá thuê"))
        self.svc.them_phong(p)
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _xoa_phong(self):
        ma = _chon(self.bang_phong)
        if not ma:
            raise ValueError("Hãy chọn phòng cần xóa.")
        self.svc.xoa_phong(ma)
        self.lam_moi_tat_ca()

    def _mo_the_phong(self, _e):
        ma = _chon(self.bang_phong)
        if ma:
            TheCanPhong(self, self.svc, self.svc.phong[ma])

    # ----- Tab Sinh viên -----
    def _tab_sinh_vien(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Sinh viên")
        form = ttk.LabelFrame(tab, text="Thông tin sinh viên", padding=6)
        form.pack(fill="x")
        self.e_ma_sv = self._o(form, "Mã SV", 0, 9)
        self.e_ten = self._o(form, "Họ tên", 1, 22)
        self.cb_gt = self._o(form, "Giới tính", 2,
                             widget=ttk.Combobox(form, values=["Nam", "Nữ"], width=6, state="readonly"))
        self.cb_gt.set("Nam")
        self.e_sdt = self._o(form, "SĐT", 3, 12)
        self.btn_sv = ttk.Button(form, text="Thêm SV", command=self._them_sv)
        self.btn_sv.grid(row=0, column=8, padx=8)

        tim = ttk.LabelFrame(tab, text="Tìm kiếm sinh viên (có thể kết hợp nhiều tiêu chí)", padding=6)
        tim.pack(fill="x", pady=(8, 0))
        self.e_tim_ma = self._o(tim, "Mã SV", 0, 10)
        self.e_tim_ten = self._o(tim, "Họ tên", 1, 18)
        self.e_tim_phong = self._o(tim, "Phòng", 2, 10)
        ttk.Button(tim, text="Tìm kiếm", command=self._loc_sinh_vien).grid(
            row=0, column=6, padx=6)
        ttk.Button(tim, text="Xóa bộ lọc", command=self._xoa_loc_sinh_vien).grid(
            row=0, column=7, padx=6)
        for o in (self.e_tim_ma, self.e_tim_ten, self.e_tim_phong):
            o.bind("<Return>", lambda _e: self._loc_sinh_vien())

        self.bang_sv = self._tao_bang(tab, [
            ("ma", "Mã SV", 90), ("ten", "Họ tên", 220), ("gt", "Giới tính", 90),
            ("sdt", "SĐT", 120), ("phong", "Phòng", 90)])

        xep = ttk.Frame(tab)
        xep.pack(fill="x", pady=6)
        ttk.Label(xep, text="Phòng:").pack(side="left")
        self.cb_phong_xep = ttk.Combobox(xep, width=10, state="readonly")
        self.cb_phong_xep.pack(side="left", padx=6)
        ttk.Button(xep, text="Xếp vào phòng (SV đang chọn)", command=self._xep_phong,
                   state=self._trang_thai_quyen("sua")).pack(side="left", padx=4)
        ttk.Button(xep, text="Trả phòng", command=self._tra_phong,
                   state=self._trang_thai_quyen("sua")).pack(side="left", padx=4)
        ttk.Button(xep, text="Xóa SV", command=self._xoa_sv,
                   state=self._trang_thai_quyen("xoa")).pack(side="left", padx=4)
        ttk.Button(xep, text="Sửa SV đã chọn", command=self._sua_sv,
                   state=self._trang_thai_quyen("sua")).pack(side="left", padx=4)
        self._ma_sv_dang_sua = None

    def _loc_sinh_vien(self):
        self.lam_moi_tat_ca()

    def _xoa_loc_sinh_vien(self):
        for o in (self.e_tim_ma, self.e_tim_ten, self.e_tim_phong):
            o.delete(0, "end")
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _them_sv(self):
        sv = SinhVien(self.e_ma_sv.get().strip(), self.e_ten.get().strip(),
                      self.cb_gt.get(), self.e_sdt.get().strip())
        if self._ma_sv_dang_sua:
            self.svc.cap_nhat_sinh_vien(self._ma_sv_dang_sua, sv)
            self._ket_thuc_sua_sv()
        else:
            self.svc.them_sinh_vien(sv)
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _sua_sv(self):
        ma = _chon(self.bang_sv)
        if not ma:
            raise ValueError("Hãy chọn một sinh viên trong bảng.")
        sv = self.svc.sinh_vien[ma]
        self.e_ma_sv.delete(0, "end")
        self.e_ma_sv.insert(0, sv.ma_sv)
        self.e_ten.delete(0, "end")
        self.e_ten.insert(0, sv.ho_ten)
        self.cb_gt.set(sv.gioi_tinh or "Nam")
        self.e_sdt.delete(0, "end")
        self.e_sdt.insert(0, sv.sdt)
        self._ma_sv_dang_sua = ma
        self.e_ma_sv.configure(state="readonly")
        self.btn_sv.configure(text="Lưu cập nhật")

    def _ket_thuc_sua_sv(self):
        self._ma_sv_dang_sua = None
        self.e_ma_sv.configure(state="normal")
        self.btn_sv.configure(text="Thêm SV")

    @xu_ly_loi
    def _xep_phong(self):
        ma = _chon(self.bang_sv)
        if not ma:
            raise ValueError("Hãy chọn một sinh viên trong bảng.")
        if not self.cb_phong_xep.get():
            raise ValueError("Hãy chọn phòng.")
        self.svc.xep_phong(ma, self.cb_phong_xep.get())
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _tra_phong(self):
        ma = _chon(self.bang_sv)
        if not ma:
            raise ValueError("Hãy chọn một sinh viên trong bảng.")
        self.svc.tra_phong(ma)
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _xoa_sv(self):
        ma = _chon(self.bang_sv)
        if not ma:
            raise ValueError("Hãy chọn một sinh viên trong bảng.")
        self.svc.xoa_sinh_vien(ma)
        self.lam_moi_tat_ca()

    # ----- Tab Sơ đồ tòa nhà (Canvas) -----
    def _tab_so_do(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Sơ đồ tòa nhà")
        bar = ttk.Frame(tab)
        bar.pack(fill="x")
        ttk.Label(bar, text="Tòa nhà:").pack(side="left")
        self.cb_toa = ttk.Combobox(bar, state="readonly", width=10)
        self.cb_toa.pack(side="left", padx=6)
        self.cb_toa.bind("<<ComboboxSelected>>", lambda e: self._ve_so_do())
        ttk.Label(bar, text=("Phòng của bạn được viền xanh - nhấp vào để xem thẻ phòng"
                             if self.la_sinh_vien else "Nhấp vào phòng để xem thẻ phòng")
                  ).pack(side="left", padx=12)

        khung = ttk.Frame(tab)
        khung.pack(fill="both", expand=True, pady=6)
        self.canvas = tk.Canvas(khung, bg="white", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        cuon = ttk.Scrollbar(khung, orient="vertical", command=self.canvas.yview)
        cuon.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=cuon.set)

    @staticmethod
    def _mau_phong(p):
        if p.so_cho_trong == 0:
            return MAU_DAY
        return MAU_TRONG if not p.ma_sv else MAU_SAP_DAY

    def _ve_so_do(self):
        c = self.canvas
        c.delete("all")
        toa = self.cb_toa.get()
        cac_tang = {}
        for p in self.svc.phong.values():
            if p.toa_nha == toa:
                cac_tang.setdefault(p.tang, []).append(p)
        y = 20
        for tang in sorted(cac_tang, reverse=True):
            c.create_text(20, y + 30, text=f"Tầng {tang}", anchor="w", font=("Segoe UI", 10, "bold"))
            x = 110
            for p in sorted(cac_tang[tang], key=lambda r: r.ma_phong):
                tag = f"phong_{p.ma_phong}"
                cua_toi = self.la_sinh_vien and p.ma_phong == self.ma_phong_cua_toi
                c.create_rectangle(x, y, x + 120, y + 62, fill=self._mau_phong(p),
                                   outline=MAU_XANH if cua_toi else "#444",
                                   width=4 if cua_toi else 2, tags=tag)
                c.create_text(x + 60, y + 20, text=p.ma_phong, font=("Segoe UI", 10, "bold"), tags=tag)
                c.create_text(x + 60, y + 44, text=f"{len(p.ma_sv)}/{p.suc_chua} SV", tags=tag)
                if not self.la_sinh_vien or cua_toi:
                    c.tag_bind(tag, "<Button-1>", lambda e, ph=p: TheCanPhong(self, self.svc, ph))
                x += 135
            y += 85
        c.configure(scrollregion=(0, 0, 800, max(y, 400)))

    # ----- Tab Hợp đồng & vi phạm -----
    def _tab_hop_dong(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Hợp đồng & vi phạm")
        hd = ttk.LabelFrame(tab, text="Hợp đồng (vàng = sắp hết hạn trong 30 ngày)", padding=6)
        hd.pack(fill="x")
        self.e_ma_hd = self._o(hd, "Mã HĐ", 0, 8, dong=0)
        self.e_hd_sv = self._o(hd, "Mã SV", 1, 8, dong=0)
        self.e_hd_ph = self._o(hd, "Mã phòng", 2, 7, dong=0)
        self.e_coc = self._o(hd, "Tiền cọc", 3, 10, dong=0)
        self.d_bd = self._o(hd, "Bắt đầu", 0, widget=tao_o_ngay(hd), dong=1)
        self.d_kt = self._o(hd, "Kết thúc", 1, widget=tao_o_ngay(hd), dong=1)
        self.btn_hd = ttk.Button(hd, text="Thêm hợp đồng", command=self._them_hd)
        self.btn_hd.grid(row=1, column=8, padx=8)
        self.bang_hd = self._tao_bang(tab, [
            ("ma", "Mã HĐ", 80), ("sv", "Mã SV", 90), ("phong", "Phòng", 80),
            ("bd", "Bắt đầu", 110), ("kt", "Kết thúc", 110), ("coc", "Tiền cọc (đ)", 120)], cao=5)
        thao_tac_hd = ttk.Frame(tab)
        thao_tac_hd.pack(fill="x")
        ttk.Button(thao_tac_hd, text="Sửa hợp đồng đã chọn",
                   command=self._sua_hd,
                   state=self._trang_thai_quyen("sua")).pack(side="left")

        vp = ttk.LabelFrame(tab, text="Vi phạm", padding=6)
        vp.pack(fill="x", pady=(8, 0))
        self.e_vp_sv = self._o(vp, "Mã SV", 0, 8)
        self.d_vp = self._o(vp, "Ngày", 1, widget=tao_o_ngay(vp))
        self.e_vp_nd = self._o(vp, "Nội dung", 2, 26)
        self.e_vp_phat = self._o(vp, "Tiền phạt (đ)", 3, 9)
        ttk.Button(vp, text="Ghi vi phạm", command=self._them_vp).grid(row=0, column=8, padx=8)
        self.bang_vp = self._tao_bang(tab, [
            ("ma", "Mã VP", 80), ("sv", "Mã SV", 90), ("ngay", "Ngày", 110),
            ("nd", "Nội dung", 320), ("phat", "Tiền phạt (đ)", 120)], cao=5)
        thao_tac_vp = ttk.Frame(tab)
        thao_tac_vp.pack(fill="x")
        ttk.Button(thao_tac_vp, text="Xóa vi phạm đã chọn",
                   command=self._xoa_vp,
                   state=self._trang_thai_quyen("xoa")).pack(side="left")
        self._ma_hd_dang_sua = None

    @xu_ly_loi
    def _them_hd(self):
        hd = HopDong(self.e_ma_hd.get().strip(), self.e_hd_sv.get().strip(), self.e_hd_ph.get().strip(),
                     lay_ngay(self.d_bd), lay_ngay(self.d_kt), lay_so(self.e_coc, "Tiền cọc"))
        if self._ma_hd_dang_sua:
            self.svc.cap_nhat_hop_dong(self._ma_hd_dang_sua, hd)
            self._ket_thuc_sua_hd()
        else:
            self.svc.them_hop_dong(hd)
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _sua_hd(self):
        ma = _chon(self.bang_hd)
        if not ma:
            raise ValueError("Hãy chọn hợp đồng cần sửa.")
        hd = self.svc.hop_dong[ma]
        for o, gia_tri in ((self.e_ma_hd, hd.ma_hd), (self.e_hd_sv, hd.ma_sv),
                           (self.e_hd_ph, hd.ma_phong), (self.e_coc, str(hd.tien_coc))):
            o.delete(0, "end")
            o.insert(0, gia_tri)
        dat_ngay(self.d_bd, hd.ngay_bat_dau)
        dat_ngay(self.d_kt, hd.ngay_ket_thuc)
        self._ma_hd_dang_sua = ma
        self.e_ma_hd.configure(state="readonly")
        self.btn_hd.configure(text="Lưu cập nhật")

    def _ket_thuc_sua_hd(self):
        self._ma_hd_dang_sua = None
        self.e_ma_hd.configure(state="normal")
        self.btn_hd.configure(text="Thêm hợp đồng")

    @xu_ly_loi
    def _them_vp(self):
        vp = ViPham(f"VP{len(self.svc.vi_pham) + 1:03d}", self.e_vp_sv.get().strip(),
                    lay_ngay(self.d_vp), self.e_vp_nd.get().strip(),
                    lay_so(self.e_vp_phat, "Tiền phạt"))
        self.svc.them_vi_pham(vp)
        self.lam_moi_tat_ca()

    @xu_ly_loi
    def _xoa_vp(self):
        ma = _chon(self.bang_vp)
        if not ma:
            raise ValueError("Hãy chọn vi phạm cần xóa.")
        self.svc.xoa_vi_pham(ma)
        self.lam_moi_tat_ca()

    # ----- Tab Hóa đơn & công nợ -----
    def _tab_hoa_don(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Điện nước & công nợ")
        form = ttk.LabelFrame(tab, text="Tạo hóa đơn tháng", padding=6)
        form.pack(fill="x")
        self.cb_phong_hd = self._o(form, "Phòng", 0,
                                   widget=ttk.Combobox(form, width=10, state="readonly"))
        self.e_thang = self._o(form, "Tháng (YYYY-MM)", 1, 9)
        self.e_thang.insert(0, date.today().strftime("%Y-%m"))
        self.e_dien = self._o(form, "Số điện (kWh)", 2, 8)
        self.e_nuoc = self._o(form, "Số nước (m³)", 3, 8)
        ttk.Button(form, text="Tạo hóa đơn", command=self._tao_hd).grid(row=0, column=8, padx=8)

        self.bang_hoa_don = self._tao_bang(tab, [
            ("ma", "Mã HĐN", 90), ("phong", "Phòng", 70), ("thang", "Tháng", 80),
            ("tp", "Tiền phòng", 110), ("td", "Tiền điện", 100), ("tn", "Tiền nước", 100),
            ("tong", "Tổng", 110), ("tt", "Trạng thái", 90)], cao=10)

        thao_tac = ttk.Frame(tab)
        thao_tac.pack(fill="x")
        ttk.Button(thao_tac, text="Đánh dấu đã thu", command=self._da_thu,
                   state=self._trang_thai_quyen("sua")).pack(side="left")
        ttk.Button(thao_tac, text="Xuất hóa đơn ra CSV", command=self._xuat_hoa_don).pack(side="left", padx=6)
        self.lbl_cong_no = ttk.Label(thao_tac, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_cong_no.pack(side="right")

    @xu_ly_loi
    def _tao_hd(self):
        ma_phong = self.cb_phong_hd.get()
        if not ma_phong:
            raise ValueError("Hãy chọn phòng.")
        hd = self.svc.tao_hoa_don(ma_phong, self.e_thang.get().strip(),
                                  lay_so(self.e_dien, "Số điện"), lay_so(self.e_nuoc, "Số nước"))
        so = len(self.svc.phong[ma_phong].ma_sv)
        chi_tiet = (f"Mỗi sinh viên ({so} người): {self.svc.chia_tien_moi_sv(hd):,.0f} đ"
                    if so else "Phòng chưa có sinh viên nên chưa chia tiền.")
        self.lam_moi_tat_ca()
        messagebox.showinfo("Đã tạo hóa đơn",
                            f"{hd.ma_hoa_don}: tổng {hd.tong_tien:,.0f} đ\n{chi_tiet}", parent=self)

    @xu_ly_loi
    def _da_thu(self):
        ma = _chon(self.bang_hoa_don)
        if not ma:
            raise ValueError("Hãy chọn hóa đơn trong bảng.")
        self.svc.danh_dau_da_thu(ma)
        self.lam_moi_tat_ca()

    def _xuat_hoa_don(self):
        duong = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                             filetypes=[("CSV", "*.csv")])
        if not duong:
            return
        cot = ["ma_hoa_don", "ma_phong", "thang", "tien_phong", "tien_dien", "tien_nuoc",
               "tong_tien", "da_thanh_toan"]
        hang = [{"ma_hoa_don": h.ma_hoa_don, "ma_phong": h.ma_phong, "thang": h.thang,
                 "tien_phong": h.tien_phong, "tien_dien": h.tien_dien, "tien_nuoc": h.tien_nuoc,
                 "tong_tien": h.tong_tien, "da_thanh_toan": h.da_thanh_toan}
                for h in self.svc.hoa_don.values()]
        storage.xuat_csv(hang, duong, cot)
        messagebox.showinfo("Hoàn tất", f"Đã xuất {len(hang)} hóa đơn.", parent=self)

    # ----- Tab Thống kê -----
    def _tab_thong_ke(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Thống kê")
        self.bang_tk = self._tao_bang(tab, [("chi_so", "Chỉ số", 350), ("gia_tri", "Giá trị", 200)], cao=12)

    # ----- Giao diện dành cho sinh viên (chỉ xem dữ liệu của chính mình) -----
    def _tim_ma_sv(self):
        """Mã sinh viên gắn với tài khoản đang đăng nhập ('' nếu chưa liên kết)."""
        ma = ma_sv_cua_tai_khoan(self.ten_dang_nhap)
        if not ma and self.ten_dang_nhap in self.svc.sinh_vien:
            ma = self.ten_dang_nhap  # tài khoản đặt tên trùng mã sinh viên
        return ma if ma in self.svc.sinh_vien else ""

    @staticmethod
    def _hang_thong_tin(cha, nhan, bien, dong):
        ttk.Label(cha, text=nhan, foreground=MAU_PHU).grid(
            row=dong, column=0, sticky="w", padx=(0, 28), pady=5)
        ttk.Label(cha, textvariable=bien, font=("Segoe UI", 10, "bold")).grid(
            row=dong, column=1, sticky="w", pady=5)

    def _tab_phong_cua_toi(self):
        tab = ttk.Frame(self.so, padding=12)
        self.so.add(tab, text="Thông tin phòng")

        banner = tk.Frame(tab, bg="#dbeafe", padx=22, pady=16)
        banner.pack(fill="x")
        self.lbl_phong_lon = tk.Label(banner, text="", bg="#dbeafe", fg=MAU_XANH_DAM,
                                      font=("Segoe UI", 22, "bold"))
        self.lbl_phong_lon.pack(anchor="w")
        self.lbl_phong_phu = tk.Label(banner, text="", bg="#dbeafe", fg=MAU_CHU,
                                      font=("Segoe UI", 10), justify="left")
        self.lbl_phong_phu.pack(anchor="w", pady=(2, 0))

        luoi = ttk.Frame(tab)
        luoi.pack(fill="x", pady=(12, 0))
        luoi.columnconfigure(0, weight=1, uniform="the")
        luoi.columnconfigure(1, weight=1, uniform="the")
        cac_khoa = ("ma_phong", "toa", "tang", "suc", "dang_o", "trong", "gia",
                    "ho_ten", "ma_sv", "gt", "sdt", "tai_khoan")
        self.sv_bien = {k: tk.StringVar(value="—") for k in cac_khoa}

        khung_phong = ttk.LabelFrame(luoi, text="Thông tin phòng", padding=12)
        khung_phong.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        for dong, (khoa, nhan) in enumerate((
                ("ma_phong", "Mã phòng"), ("toa", "Tòa nhà"), ("tang", "Tầng"),
                ("suc", "Sức chứa"), ("dang_o", "Đang ở"), ("trong", "Chỗ còn trống"),
                ("gia", "Giá thuê"))):
            self._hang_thong_tin(khung_phong, nhan, self.sv_bien[khoa], dong)

        khung_ca_nhan = ttk.LabelFrame(luoi, text="Thông tin cá nhân", padding=12)
        khung_ca_nhan.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        for dong, (khoa, nhan) in enumerate((
                ("ho_ten", "Họ tên"), ("ma_sv", "Mã sinh viên"), ("gt", "Giới tính"),
                ("sdt", "Số điện thoại"), ("tai_khoan", "Tài khoản"))):
            self._hang_thong_tin(khung_ca_nhan, nhan, self.sv_bien[khoa], dong)

        khung_ban = ttk.LabelFrame(tab, text="Sinh viên cùng phòng", padding=8)
        khung_ban.pack(fill="both", expand=True, pady=(12, 0))
        self.bang_ban = self._tao_bang(khung_ban, [
            ("ma", "Mã SV", 120), ("ten", "Họ tên", 260), ("gt", "Giới tính", 100)], cao=5)

    def _tab_hop_dong_sv(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Hợp đồng")
        ttk.Label(tab, text="Hợp đồng của bạn (vàng = sắp hết hạn trong 30 ngày)",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.bang_hd = self._tao_bang(tab, [
            ("ma", "Mã HĐ", 90), ("sv", "Mã SV", 110), ("phong", "Phòng", 90),
            ("bd", "Bắt đầu", 120), ("kt", "Kết thúc", 120), ("coc", "Tiền cọc (đ)", 130)], cao=8)
        self.lbl_hd_trong = ttk.Label(tab, text="", foreground=MAU_PHU)
        self.lbl_hd_trong.pack(anchor="w")

    def _tab_hoa_don_sv(self):
        tab = ttk.Frame(self.so, padding=8)
        self.so.add(tab, text="Điện nước & công nợ")
        self.lbl_hd_phong = ttk.Label(tab, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_hd_phong.pack(anchor="w")
        self.bang_hoa_don = self._tao_bang(tab, [
            ("ma", "Mã HĐN", 90), ("phong", "Phòng", 70), ("thang", "Tháng", 80),
            ("tp", "Tiền phòng", 110), ("td", "Tiền điện", 100), ("tn", "Tiền nước", 100),
            ("tong", "Tổng", 110), ("tt", "Trạng thái", 90)], cao=10)
        chan = ttk.Frame(tab)
        chan.pack(fill="x")
        ttk.Label(chan, text="Dòng đỏ: chưa thu • Dòng không tô màu: đã thu",
                  foreground=MAU_PHU).pack(side="left")
        self.lbl_cong_no = ttk.Label(chan, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_cong_no.pack(side="right")

    def _lam_moi_sinh_vien(self):
        svc = self.svc
        sv = svc.sinh_vien.get(self.ma_sv)
        phong = next((p for p in svc.phong.values() if self.ma_sv and self.ma_sv in p.ma_sv), None)
        self.ma_phong_cua_toi = phong.ma_phong if phong else ""

        # --- Tab Thông tin phòng ---
        dat = lambda khoa, gia_tri: self.sv_bien[khoa].set(gia_tri)
        dat("tai_khoan", self.ten_dang_nhap or "—")
        for khoa, gia_tri in (("ho_ten", sv.ho_ten if sv else "—"),
                              ("ma_sv", sv.ma_sv if sv else "—"),
                              ("gt", (sv.gioi_tinh or "—") if sv else "—"),
                              ("sdt", (sv.sdt or "—") if sv else "—")):
            dat(khoa, gia_tri)
        if phong:
            trang_thai = "Đã đầy" if phong.so_cho_trong == 0 else f"Còn {phong.so_cho_trong} chỗ"
            self.lbl_phong_lon.config(text=f"Phòng {phong.ma_phong}")
            self.lbl_phong_phu.config(text=f"Tòa {phong.toa_nha} • Tầng {phong.tang} • {trang_thai}")
            for khoa, gia_tri in (("ma_phong", phong.ma_phong), ("toa", phong.toa_nha),
                                  ("tang", str(phong.tang)), ("suc", f"{phong.suc_chua} chỗ"),
                                  ("dang_o", f"{len(phong.ma_sv)} sinh viên"),
                                  ("trong", f"{phong.so_cho_trong} chỗ"),
                                  ("gia", f"{phong.gia_thue:,.0f} đ/tháng")):
                dat(khoa, gia_tri)
        else:
            for khoa in ("ma_phong", "toa", "tang", "suc", "dang_o", "trong", "gia"):
                dat(khoa, "—")
            if sv:
                self.lbl_phong_lon.config(text="Chưa có phòng")
                self.lbl_phong_phu.config(text=f"{sv.ho_ten} chưa được xếp vào phòng nào.")
            else:
                self.lbl_phong_lon.config(text="Chưa liên kết sinh viên")
                self.lbl_phong_phu.config(
                    text="Tài khoản này chưa gắn với mã sinh viên nào.\n"
                         "Hãy liên hệ quản trị viên hoặc đăng ký lại với đúng mã sinh viên.")
        b = self.bang_ban
        b.delete(*b.get_children())
        for ma in (phong.ma_sv if phong else []):
            ban = svc.sinh_vien.get(ma)
            if ban:
                b.insert("", "end", iid=ma, values=(
                    ban.ma_sv, ban.ho_ten + ("  (bạn)" if ma == self.ma_sv else ""),
                    ban.gioi_tinh))

        # --- Tab Sơ đồ tòa nhà ---
        toa = sorted({p.toa_nha for p in svc.phong.values()})
        self.cb_toa["values"] = toa
        if toa and self.cb_toa.get() not in toa:
            self.cb_toa.set(phong.toa_nha if phong else toa[0])
        self._ve_so_do()

        # --- Tab Hợp đồng: chỉ hợp đồng của chính sinh viên ---
        hop_dong = [h for h in svc.hop_dong.values() if self.ma_sv and h.ma_sv == self.ma_sv]
        sap_het_han = {h.ma_hd for h in svc.hop_dong_sap_het_han(30)}
        b = self.bang_hd
        b.delete(*b.get_children())
        for h in hop_dong:
            b.insert("", "end", iid=h.ma_hd, tags=("sap",) if h.ma_hd in sap_het_han else (),
                     values=(h.ma_hd, h.ma_sv, h.ma_phong, h.ngay_bat_dau, h.ngay_ket_thuc,
                             f"{h.tien_coc:,.0f}"))
        self.lbl_hd_trong.config(text="" if hop_dong else "Bạn chưa có hợp đồng nào.")

        # --- Tab Điện nước & công nợ: chỉ hóa đơn của phòng mình ---
        hoa_don = [h for h in svc.hoa_don.values()
                   if self.ma_phong_cua_toi and h.ma_phong == self.ma_phong_cua_toi]
        b = self.bang_hoa_don
        b.delete(*b.get_children())
        for h in hoa_don:
            b.insert("", "end", iid=h.ma_hoa_don, tags=() if h.da_thanh_toan else ("day",),
                     values=(h.ma_hoa_don, h.ma_phong, h.thang, f"{h.tien_phong:,.0f}",
                             f"{h.tien_dien:,.0f}", f"{h.tien_nuoc:,.0f}", f"{h.tong_tien:,.0f}",
                             "Đã thu" if h.da_thanh_toan else "Chưa thu"))
        chua_thu = [h for h in hoa_don if not h.da_thanh_toan]
        no_phong = sum(h.tong_tien for h in chua_thu)
        phan_toi = sum(svc.chia_tien_moi_sv(h) for h in chua_thu)
        self.lbl_hd_phong.config(
            text=f"Hóa đơn phòng {self.ma_phong_cua_toi}" if phong else "Bạn chưa có phòng nên chưa có hóa đơn.")
        self.lbl_cong_no.config(
            text=f"Công nợ chưa thu của phòng: {no_phong:,.0f} đ  •  Phần của bạn: {phan_toi:,.0f} đ")

        # --- Tab Thống kê: số liệu của bạn + tình hình chung (không lộ dữ liệu người khác) ---
        chung = svc.thong_ke()
        dong_thong_ke = [
            ("Phòng của bạn", phong.ma_phong if phong else "Chưa có phòng"),
            ("Số sinh viên cùng phòng", max(len(phong.ma_sv) - 1, 0) if phong else 0),
            ("Chỗ còn trống trong phòng", phong.so_cho_trong if phong else 0),
            ("Số hợp đồng của bạn", len(hop_dong)),
            ("Hợp đồng sắp hết hạn (30 ngày)", sum(1 for h in hop_dong if h.ma_hd in sap_het_han)),
            ("Số hóa đơn của phòng", len(hoa_don)),
            ("Hóa đơn đã thu", len(hoa_don) - len(chua_thu)),
            ("Hóa đơn chưa thu", len(chua_thu)),
            ("Công nợ chưa thu của phòng (đ)", no_phong),
            ("Phần công nợ của bạn (đ)", phan_toi),
            ("Tổng số phòng toàn ký túc xá", chung["Tổng số phòng"]),
            ("Số chỗ còn trống toàn ký túc xá", chung["Số chỗ còn trống"]),
        ]
        b = self.bang_tk
        b.delete(*b.get_children())
        for ten, gia_tri in dong_thong_ke:
            b.insert("", "end", values=(ten, gia_tri if isinstance(gia_tri, str) else f"{gia_tri:,.0f}"))

        # --- Tiêu đề ---
        self.lbl_tom_tat.config(
            text=(f"Phòng {phong.ma_phong}  •  Tòa {phong.toa_nha}  •  Tầng {phong.tang}" if phong
                  else "Chưa có phòng"))
        self.trang_thai.set("Dữ liệu đã được làm mới")

    # ----- Lưu / nhập / xuất -----
    def _luu(self):
        storage.luu_json(self.svc.to_dict(), FILE_DU_LIEU)
        self.trang_thai.set(f"Đã lưu dữ liệu lúc {datetime.now().strftime('%H:%M:%S')}")
        messagebox.showinfo("Đã lưu", f"Dữ liệu đã lưu tại:\n{FILE_DU_LIEU}", parent=self)

    def _thoat(self):
        if not self.la_sinh_vien:
            storage.luu_json(self.svc.to_dict(), FILE_DU_LIEU)
        self.destroy()

    def _dang_xuat(self):
        if not self.la_sinh_vien:
            storage.luu_json(self.svc.to_dict(), FILE_DU_LIEU)
        self.dang_xuat = True
        self.destroy()

    @xu_ly_loi
    def _nhap_csv(self):
        duong = filedialog.askopenfilename(parent=self, filetypes=[("CSV", "*.csv")])
        if not duong:
            return
        so = self.svc.nhap_sinh_vien_tu_dong(storage.doc_csv(duong))
        self.lam_moi_tat_ca()
        self.trang_thai.set(f"Đã nhập {so} sinh viên từ CSV.")
        messagebox.showinfo("Hoàn tất", f"Đã nhập {so} sinh viên mới.", parent=self)

    def _xuat_sv_csv(self):
        duong = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                                             filetypes=[("CSV", "*.csv")])
        if not duong:
            return
        cot = ["ma_sv", "ho_ten", "gioi_tinh", "sdt", "ma_phong"]
        hang = [{k: getattr(s, k) for k in cot} for s in self.svc.sinh_vien.values()]
        storage.xuat_csv(hang, duong, cot)
        messagebox.showinfo("Hoàn tất", f"Đã xuất {len(hang)} sinh viên.", parent=self)

    # ----- Làm mới toàn bộ giao diện -----
    def lam_moi_tat_ca(self):
        if self.la_sinh_vien:
            self._lam_moi_sinh_vien()
            return
        b = self.bang_phong
        b.delete(*b.get_children())
        for p in self.svc.phong.values():
            tag = "day" if p.so_cho_trong == 0 else ("trong" if not p.ma_sv else "sap")
            b.insert("", "end", iid=p.ma_phong, tags=(tag,),
                     values=(p.ma_phong, p.toa_nha, p.tang, p.suc_chua, p.so_cho_trong,
                             f"{p.gia_thue:,.0f}"))

        b = self.bang_sv
        b.delete(*b.get_children())
        loc_ma = self.e_tim_ma.get().strip().casefold()
        loc_ten = self.e_tim_ten.get().strip().casefold()
        loc_phong = self.e_tim_phong.get().strip().casefold()
        for s in self.svc.sinh_vien.values():
            if ((loc_ma and loc_ma not in s.ma_sv.casefold())
                    or (loc_ten and loc_ten not in s.ho_ten.casefold())
                    or (loc_phong and loc_phong not in s.ma_phong.casefold())):
                continue
            b.insert("", "end", iid=s.ma_sv,
                     values=(s.ma_sv, s.ho_ten, s.gioi_tinh, s.sdt, s.ma_phong or "—"))

        sap_het_han = {h.ma_hd for h in self.svc.hop_dong_sap_het_han(30)}
        b = self.bang_hd
        b.delete(*b.get_children())
        for h in self.svc.hop_dong.values():
            b.insert("", "end", iid=h.ma_hd, tags=("sap",) if h.ma_hd in sap_het_han else (),
                     values=(h.ma_hd, h.ma_sv, h.ma_phong, h.ngay_bat_dau, h.ngay_ket_thuc,
                             f"{h.tien_coc:,.0f}"))

        b = self.bang_vp
        b.delete(*b.get_children())
        for v in self.svc.vi_pham.values():
            b.insert("", "end", iid=v.ma_vp,
                     values=(v.ma_vp, v.ma_sv, v.ngay, v.noi_dung, f"{v.tien_phat:,.0f}"))

        b = self.bang_hoa_don
        b.delete(*b.get_children())
        for h in self.svc.hoa_don.values():
            b.insert("", "end", iid=h.ma_hoa_don, tags=() if h.da_thanh_toan else ("day",),
                     values=(h.ma_hoa_don, h.ma_phong, h.thang, f"{h.tien_phong:,.0f}",
                             f"{h.tien_dien:,.0f}", f"{h.tien_nuoc:,.0f}", f"{h.tong_tien:,.0f}",
                             "Đã thu" if h.da_thanh_toan else "Chưa thu"))
        self.lbl_cong_no.config(text=f"Tổng công nợ chưa thu: {self.svc.cong_no():,.0f} đ")

        b = self.bang_tk
        b.delete(*b.get_children())
        for k, v in self.svc.thong_ke().items():
            b.insert("", "end", values=(k, f"{v:,.0f}"))

        ds_phong = sorted(self.svc.phong)
        self.cb_phong_xep["values"] = ds_phong
        self.cb_phong_hd["values"] = ds_phong
        toa = sorted({p.toa_nha for p in self.svc.phong.values()})
        self.cb_toa["values"] = toa
        if toa and self.cb_toa.get() not in toa:
            self.cb_toa.set(toa[0])
        self._ve_so_do()
        tk = self.svc.thong_ke()
        self.lbl_tom_tat.config(
            text=f"{tk['Tổng số phòng']} phòng  •  {tk['Tổng số sinh viên']} sinh viên  •  "
                 f"{tk['Số chỗ còn trống']} chỗ trống"
        )
        self.trang_thai.set("Dữ liệu đã được làm mới")
