"""Nghiệp vụ: phòng, sinh viên, xếp phòng, hợp đồng, vi phạm, hóa đơn, thống kê, phân quyền."""
from dataclasses import asdict
from datetime import date, datetime, timedelta
import hashlib
import hmac
import os
import secrets

from models import Phong, SinhVien, HopDong, HoaDon, ViPham
import storage

# Phân quyền theo vai trò
QUYEN = {
    "admin": {"them", "sua", "xoa", "xem"},
    "nhan_vien": {"them", "xem"},
    "sinh_vien": {"xem"},
}

TAI_KHOAN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "data", "tai_khoan.json")
SO_VONG_BAM = 120_000


def _bam_mat_khau(mat_khau, muoi):
    return hashlib.pbkdf2_hmac(
        "sha256", mat_khau.encode("utf-8"), bytes.fromhex(muoi), SO_VONG_BAM
    ).hex()


def _doc_tai_khoan():
    if not os.path.exists(TAI_KHOAN_FILE):
        return []
    return storage.doc_json(TAI_KHOAN_FILE)


def xac_thuc(ten_dang_nhap, mat_khau, vai_tro):
    """Kiểm tra thông tin đăng nhập từ data/tai_khoan.json."""
    for tai_khoan in _doc_tai_khoan():
        if (tai_khoan.get("ten_dang_nhap") == ten_dang_nhap
                and tai_khoan.get("vai_tro") == vai_tro):
            ma_bam = _bam_mat_khau(mat_khau, tai_khoan["muoi"])
            return hmac.compare_digest(ma_bam, tai_khoan["mat_khau_bam"])
    return False


def doi_mat_khau(ten_dang_nhap, vai_tro, mat_khau_cu, mat_khau_moi):
    """Đổi mật khẩu sau khi xác minh mật khẩu hiện tại."""
    if not mat_khau_moi:
        raise ValueError("Mật khẩu mới không được để trống.")
    if len(mat_khau_moi) < 6:
        raise ValueError("Mật khẩu mới phải có ít nhất 6 ký tự.")
    if not xac_thuc(ten_dang_nhap, mat_khau_cu, vai_tro):
        raise ValueError("Mật khẩu hiện tại không đúng.")
    tai_khoan = _doc_tai_khoan()
    for tai_khoan_item in tai_khoan:
        if (tai_khoan_item.get("ten_dang_nhap") == ten_dang_nhap
                and tai_khoan_item.get("vai_tro") == vai_tro):
            muoi = secrets.token_bytes(16).hex()
            tai_khoan_item["muoi"] = muoi
            tai_khoan_item["mat_khau_bam"] = _bam_mat_khau(mat_khau_moi, muoi)
            storage.luu_json(tai_khoan, TAI_KHOAN_FILE)
            return
    raise ValueError("Không tìm thấy tài khoản.")


def _ma_sinh_vien_hien_co():
    """Tập mã sinh viên đang có (đọc data/du_lieu.json, chưa có thì dùng dữ liệu mẫu)."""
    if os.path.exists(storage.DUONG_DAN_MAC_DINH):
        du_lieu = storage.doc_json(storage.DUONG_DAN_MAC_DINH)
        return {x["ma_sv"] for x in du_lieu.get("sinh_vien", [])}
    return set(tao_du_lieu_mau(DormService("admin")).sinh_vien)


def ma_sv_cua_tai_khoan(ten_dang_nhap):
    """Mã sinh viên gắn với tài khoản sinh viên (chuỗi rỗng nếu chưa liên kết)."""
    for tai_khoan in _doc_tai_khoan():
        if (tai_khoan.get("ten_dang_nhap") == ten_dang_nhap
                and tai_khoan.get("vai_tro") == "sinh_vien"):
            return tai_khoan.get("ma_sv", "")
    return ""


def dang_ky_tai_khoan(ten_dang_nhap, mat_khau, vai_tro="sinh_vien", ma_sv=None):
    """Tạo tài khoản mới và lưu mật khẩu dưới dạng PBKDF2-HMAC.

    Với tài khoản sinh viên, ma_sv liên kết tài khoản với một sinh viên đã có trong
    hệ thống để giao diện chỉ hiển thị phòng/hợp đồng/hóa đơn của chính sinh viên đó.
    """
    ten_dang_nhap = ten_dang_nhap.strip()
    if not ten_dang_nhap or not mat_khau:
        raise ValueError("Tên đăng nhập và mật khẩu không được để trống.")
    if len(ten_dang_nhap) < 3:
        raise ValueError("Tên đăng nhập phải có ít nhất 3 ký tự.")
    if len(mat_khau) < 6:
        raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")
    if vai_tro != "sinh_vien":
        raise ValueError("Chỉ được đăng ký tài khoản sinh viên.")

    tai_khoan = _doc_tai_khoan()
    if any(x.get("ten_dang_nhap") == ten_dang_nhap for x in tai_khoan):
        raise ValueError("Tên đăng nhập đã tồn tại.")
    if ma_sv is not None:
        ma_sv = ma_sv.strip()
        if not ma_sv:
            raise ValueError("Vui lòng nhập mã sinh viên.")
        if ma_sv not in _ma_sinh_vien_hien_co():
            raise ValueError("Mã sinh viên chưa có trong hệ thống. Hãy liên hệ quản trị viên.")
        if any(x.get("ma_sv") == ma_sv for x in tai_khoan):
            raise ValueError("Mã sinh viên này đã có tài khoản.")
    muoi = secrets.token_bytes(16).hex()
    moi = {
        "ten_dang_nhap": ten_dang_nhap,
        "vai_tro": vai_tro,
        "muoi": muoi,
        "mat_khau_bam": _bam_mat_khau(mat_khau, muoi),
    }
    if ma_sv:
        moi["ma_sv"] = ma_sv
    tai_khoan.append(moi)
    storage.luu_json(tai_khoan, TAI_KHOAN_FILE)


def tao_tai_khoan_nhan_vien(ten_dang_nhap, mat_khau):
    """Tạo tài khoản nhân viên dùng khi quản trị viên khởi tạo tài khoản nội bộ."""
    ten_dang_nhap = ten_dang_nhap.strip()
    if not ten_dang_nhap or not mat_khau:
        raise ValueError("Tên đăng nhập và mật khẩu không được để trống.")
    if len(ten_dang_nhap) < 3:
        raise ValueError("Tên đăng nhập phải có ít nhất 3 ký tự.")
    if len(mat_khau) < 6:
        raise ValueError("Mật khẩu phải có ít nhất 6 ký tự.")

    tai_khoan = _doc_tai_khoan()
    if any(x.get("ten_dang_nhap") == ten_dang_nhap for x in tai_khoan):
        raise ValueError("Tên đăng nhập đã tồn tại.")

    muoi = secrets.token_bytes(16).hex()
    tai_khoan.append({
        "ten_dang_nhap": ten_dang_nhap,
        "vai_tro": "nhan_vien",
        "muoi": muoi,
        "mat_khau_bam": _bam_mat_khau(mat_khau, muoi),
    })
    storage.luu_json(tai_khoan, TAI_KHOAN_FILE)


class DormService:
    def __init__(self, vai_tro="admin"):
        self.vai_tro = vai_tro
        self.gia_dien = 3500   # VNĐ / kWh
        self.gia_nuoc = 15000  # VNĐ / m³
        self.phong = {}
        self.sinh_vien = {}
        self.hop_dong = {}
        self.hoa_don = {}
        self.vi_pham = {}

    # ---------- Tiện ích ----------
    def _kiem_quyen(self, hanh_dong):
        if hanh_dong not in QUYEN.get(self.vai_tro, set()):
            raise PermissionError(f"Vai trò '{self.vai_tro}' không có quyền thực hiện thao tác này.")

    @staticmethod
    def _lay(kho, ma, ten):
        if ma not in kho:
            raise ValueError(f"Không tìm thấy {ten} có mã '{ma}'.")
        return kho[ma]

    @staticmethod
    def _kiem_trung(kho, ma, ten):
        if not ma:
            raise ValueError(f"Mã {ten.lower()} không được để trống.")
        if ma in kho:
            raise ValueError(f"{ten} có mã '{ma}' đã tồn tại.")

    # ---------- Phòng ----------
    def them_phong(self, p):
        self._kiem_quyen("them")
        self._kiem_trung(self.phong, p.ma_phong, "Phòng")
        if p.suc_chua <= 0:
            raise ValueError("Sức chứa phải lớn hơn 0.")
        if p.gia_thue < 0:
            raise ValueError("Giá thuê không được âm.")
        self.phong[p.ma_phong] = p

    def xoa_phong(self, ma_phong):
        self._kiem_quyen("xoa")
        p = self._lay(self.phong, ma_phong, "phòng")
        if p.ma_sv:
            raise ValueError("Phòng còn sinh viên đang ở, hãy trả phòng trước.")
        del self.phong[ma_phong]

    # ---------- Sinh viên ----------
    def them_sinh_vien(self, sv):
        self._kiem_quyen("them")
        self._kiem_trung(self.sinh_vien, sv.ma_sv, "Sinh viên")
        self.sinh_vien[sv.ma_sv] = sv

    def cap_nhat_sinh_vien(self, ma_sv, sv):
        self._kiem_quyen("sua")
        cu = self._lay(self.sinh_vien, ma_sv, "sinh viên")
        if sv.ma_sv != ma_sv:
            raise ValueError("Không được thay đổi mã sinh viên khi cập nhật.")
        sv.ma_phong = cu.ma_phong
        self.sinh_vien[ma_sv] = sv

    def xoa_sinh_vien(self, ma_sv):
        self._kiem_quyen("xoa")
        self._lay(self.sinh_vien, ma_sv, "sinh viên")
        if self.sinh_vien[ma_sv].ma_phong:
            self.tra_phong(ma_sv)
        del self.sinh_vien[ma_sv]

    def nhap_sinh_vien_tu_dong(self, hang):
        """Nhập danh sách từ CSV (cột: ma_sv, ho_ten, gioi_tinh, sdt). Bỏ qua mã đã tồn tại."""
        so = 0
        for r in hang:
            ma = r["ma_sv"].strip()
            if not ma or ma in self.sinh_vien:
                continue
            self.them_sinh_vien(SinhVien(ma, r["ho_ten"].strip(),
                                         r.get("gioi_tinh", "").strip(), r.get("sdt", "").strip()))
            so += 1
        return so

    # ---------- Xếp / trả phòng ----------
    def xep_phong(self, ma_sv, ma_phong):
        self._kiem_quyen("sua")
        sv = self._lay(self.sinh_vien, ma_sv, "sinh viên")
        p = self._lay(self.phong, ma_phong, "phòng")
        if sv.ma_phong == ma_phong:
            raise ValueError(f"Sinh viên đã ở phòng {ma_phong}.")
        if p.so_cho_trong <= 0:
            raise ValueError(f"Phòng {ma_phong} đã hết chỗ.")
        if sv.ma_phong:
            self.tra_phong(ma_sv)  # chuyển phòng: trả phòng cũ trước
        p.ma_sv.append(ma_sv)
        sv.ma_phong = ma_phong

    def tra_phong(self, ma_sv):
        self._kiem_quyen("sua")
        sv = self._lay(self.sinh_vien, ma_sv, "sinh viên")
        if sv.ma_phong:
            self.phong[sv.ma_phong].ma_sv.remove(ma_sv)
            sv.ma_phong = ""

    # ---------- Hợp đồng ----------
    def them_hop_dong(self, hd):
        self._kiem_quyen("them")
        self._kiem_trung(self.hop_dong, hd.ma_hd, "Hợp đồng")
        self._kiem_tra_hop_dong(hd)
        self.hop_dong[hd.ma_hd] = hd

    def cap_nhat_hop_dong(self, ma_hd, hd):
        self._kiem_quyen("sua")
        self._lay(self.hop_dong, ma_hd, "hợp đồng")
        if hd.ma_hd != ma_hd:
            raise ValueError("Không được thay đổi mã hợp đồng khi cập nhật.")
        self._kiem_tra_hop_dong(hd)
        self.hop_dong[ma_hd] = hd

    def _kiem_tra_hop_dong(self, hd):
        self._lay(self.sinh_vien, hd.ma_sv, "sinh viên")
        self._lay(self.phong, hd.ma_phong, "phòng")
        try:
            bd = date.fromisoformat(hd.ngay_bat_dau)
            kt = date.fromisoformat(hd.ngay_ket_thuc)
        except ValueError:
            raise ValueError("Ngày hợp đồng phải có dạng YYYY-MM-DD.")
        if kt <= bd:
            raise ValueError("Ngày kết thúc phải sau ngày bắt đầu.")
        if hd.tien_coc < 0:
            raise ValueError("Tiền cọc không được âm.")

    def hop_dong_sap_het_han(self, so_ngay=30, hom_nay=None):
        hom_nay = hom_nay or date.today()
        gioi_han = hom_nay + timedelta(days=so_ngay)
        return [hd for hd in self.hop_dong.values()
                if hom_nay <= date.fromisoformat(hd.ngay_ket_thuc) <= gioi_han]

    # ---------- Vi phạm ----------
    def them_vi_pham(self, vp):
        self._kiem_quyen("them")
        self._kiem_trung(self.vi_pham, vp.ma_vp, "Vi phạm")
        self._lay(self.sinh_vien, vp.ma_sv, "sinh viên")
        if vp.tien_phat < 0:
            raise ValueError("Tiền phạt không được âm.")
        self.vi_pham[vp.ma_vp] = vp

    def xoa_vi_pham(self, ma_vp):
        self._kiem_quyen("xoa")
        self._lay(self.vi_pham, ma_vp, "vi phạm")
        del self.vi_pham[ma_vp]

    # ---------- Hóa đơn điện nước, công nợ ----------
    def tao_hoa_don(self, ma_phong, thang, so_dien, so_nuoc):
        self._kiem_quyen("them")
        p = self._lay(self.phong, ma_phong, "phòng")
        try:
            datetime.strptime(thang, "%Y-%m")
        except ValueError:
            raise ValueError("Tháng phải có dạng YYYY-MM, ví dụ 2026-10.")
        if so_dien < 0 or so_nuoc < 0:
            raise ValueError("Chỉ số điện/nước không được âm.")
        ma = f"HDN{len(self.hoa_don) + 1:04d}"
        hd = HoaDon(ma, ma_phong, thang, so_dien, so_nuoc,
                    p.gia_thue, so_dien * self.gia_dien, so_nuoc * self.gia_nuoc)
        self.hoa_don[ma] = hd
        return hd

    def chia_tien_moi_sv(self, hd):
        so = len(self.phong[hd.ma_phong].ma_sv)
        return hd.tong_tien / so if so else hd.tong_tien

    def danh_dau_da_thu(self, ma_hd):
        self._kiem_quyen("sua")
        self._lay(self.hoa_don, ma_hd, "hóa đơn").da_thanh_toan = True

    def cong_no(self):
        return sum(hd.tong_tien for hd in self.hoa_don.values() if not hd.da_thanh_toan)

    # ---------- Thống kê ----------
    def thong_ke(self):
        tong_cho = sum(p.suc_chua for p in self.phong.values())
        dang_o = sum(len(p.ma_sv) for p in self.phong.values())
        return {
            "Tổng số phòng": len(self.phong),
            "Tổng số chỗ": tong_cho,
            "Số chỗ còn trống": tong_cho - dang_o,
            "Phòng trống hoàn toàn": sum(1 for p in self.phong.values() if not p.ma_sv),
            "Phòng đã đầy": sum(1 for p in self.phong.values() if p.so_cho_trong == 0),
            "Tổng số sinh viên": len(self.sinh_vien),
            "Hợp đồng sắp hết hạn (30 ngày)": len(self.hop_dong_sap_het_han(30)),
            "Số vi phạm": len(self.vi_pham),
            "Công nợ chưa thu (đ)": self.cong_no(),
        }

    # ---------- Lưu / đọc ----------
    def to_dict(self):
        return {
            "gia_dien": self.gia_dien,
            "gia_nuoc": self.gia_nuoc,
            "phong": [asdict(x) for x in self.phong.values()],
            "sinh_vien": [asdict(x) for x in self.sinh_vien.values()],
            "hop_dong": [asdict(x) for x in self.hop_dong.values()],
            "hoa_don": [asdict(x) for x in self.hoa_don.values()],
            "vi_pham": [asdict(x) for x in self.vi_pham.values()],
        }

    @classmethod
    def from_dict(cls, d, vai_tro="admin"):
        s = cls(vai_tro)
        s.gia_dien = d.get("gia_dien", s.gia_dien)
        s.gia_nuoc = d.get("gia_nuoc", s.gia_nuoc)
        s.phong = {x["ma_phong"]: Phong(**x) for x in d.get("phong", [])}
        s.sinh_vien = {x["ma_sv"]: SinhVien(**x) for x in d.get("sinh_vien", [])}
        s.hop_dong = {x["ma_hd"]: HopDong(**x) for x in d.get("hop_dong", [])}
        s.hoa_don = {x["ma_hoa_don"]: HoaDon(**x) for x in d.get("hoa_don", [])}
        s.vi_pham = {x["ma_vp"]: ViPham(**x) for x in d.get("vi_pham", [])}
        return s


def tao_du_lieu_mau(svc):
    """Tạo dữ liệu mẫu để chạy thử ngay."""
    for toa in ("A", "B"):
        for tang in (1, 2, 3):
            for i in range(1, 5):
                ma = f"{toa}{tang}{i:02d}"
                svc.phong[ma] = Phong(ma, toa, tang, 4, 900_000 if toa == "A" else 1_200_000)

    ds_sv = [
        ("SV001", "Nguyễn Văn An", "Nam", "0901000001"),
        ("SV002", "Trần Thị Bích", "Nữ", "0901000002"),
        ("SV003", "Lê Minh Cường", "Nam", "0901000003"),
        ("SV004", "Phạm Thu Dung", "Nữ", "0901000004"),
        ("SV005", "Hoàng Gia Huy", "Nam", "0901000005"),
    ]
    for ma, ten, gt, sdt in ds_sv:
        svc.sinh_vien[ma] = SinhVien(ma, ten, gt, sdt)

    for ma_sv, ma_phong in [("SV001", "A101"), ("SV002", "A101"), ("SV003", "A102"), ("SV004", "B201")]:
        svc.xep_phong(ma_sv, ma_phong)

    svc.hop_dong["HD001"] = HopDong("HD001", "SV001", "A101", "2026-09-01", "2027-06-30", 1_000_000)
    svc.hop_dong["HD002"] = HopDong("HD002", "SV002", "A101", "2025-11-01", "2026-11-10", 1_000_000)
    svc.vi_pham["VP001"] = ViPham("VP001", "SV003", "2026-10-05", "Nấu ăn trong phòng", 200_000)
    svc.tao_hoa_don("A101", "2026-09", 120, 8)
    return svc
