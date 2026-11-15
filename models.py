"""Các lớp dữ liệu (model) của ứng dụng quản lý ký túc xá."""
from dataclasses import dataclass, field


@dataclass
class Phong:
    ma_phong: str
    toa_nha: str
    tang: int
    suc_chua: int
    gia_thue: float  # VNĐ / tháng
    ma_sv: list = field(default_factory=list)

    @property
    def so_cho_trong(self):
        return self.suc_chua - len(self.ma_sv)


@dataclass
class SinhVien:
    ma_sv: str
    ho_ten: str
    gioi_tinh: str
    sdt: str = ""
    ma_phong: str = ""


@dataclass
class HopDong:
    ma_hd: str
    ma_sv: str
    ma_phong: str
    ngay_bat_dau: str  # YYYY-MM-DD
    ngay_ket_thuc: str  # YYYY-MM-DD
    tien_coc: float = 0


@dataclass
class HoaDon:
    ma_hoa_don: str
    ma_phong: str
    thang: str  # YYYY-MM
    so_dien: float
    so_nuoc: float
    tien_phong: float
    tien_dien: float
    tien_nuoc: float
    da_thanh_toan: bool = False

    @property
    def tong_tien(self):
        return self.tien_phong + self.tien_dien + self.tien_nuoc


@dataclass
class ViPham:
    ma_vp: str
    ma_sv: str
    ngay: str  # YYYY-MM-DD
    noi_dung: str
    tien_phat: float = 0
