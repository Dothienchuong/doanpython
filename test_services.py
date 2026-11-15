"""Kiểm thử nghiệp vụ. Chạy: python -m unittest test_services -v"""
import unittest
from datetime import date

from models import Phong, SinhVien, HopDong, ViPham
from services import DormService, tao_du_lieu_mau, xac_thuc


class TestDormService(unittest.TestCase):
    def setUp(self):
        self.svc = DormService("admin")
        self.svc.them_phong(Phong("A101", "A", 1, 2, 900_000))
        for ma, ten in [("SV1", "An"), ("SV2", "Bình"), ("SV3", "Cường")]:
            self.svc.them_sinh_vien(SinhVien(ma, ten, "Nam"))

    def test_khong_xep_vuot_suc_chua(self):
        self.svc.xep_phong("SV1", "A101")
        self.svc.xep_phong("SV2", "A101")
        with self.assertRaises(ValueError):
            self.svc.xep_phong("SV3", "A101")

    def test_chuyen_phong(self):
        self.svc.them_phong(Phong("A102", "A", 1, 2, 900_000))
        self.svc.xep_phong("SV1", "A101")
        self.svc.xep_phong("SV1", "A102")
        self.assertEqual(self.svc.phong["A101"].ma_sv, [])
        self.assertEqual(self.svc.sinh_vien["SV1"].ma_phong, "A102")

    def test_phan_quyen(self):
        self.svc.vai_tro = "khach"
        with self.assertRaises(PermissionError):
            self.svc.them_phong(Phong("B1", "B", 1, 2, 1))

    def test_nhan_vien_chi_duoc_them_khong_duoc_sua_xoa(self):
        self.svc.vai_tro = "nhan_vien"
        self.svc.them_phong(Phong("B1", "B", 1, 2, 1))
        self.svc.them_sinh_vien(SinhVien("SV4", "Dũng", "Nam"))
        with self.assertRaises(PermissionError):
            self.svc.cap_nhat_sinh_vien("SV4", SinhVien("SV4", "Dũng mới", "Nam"))
        with self.assertRaises(PermissionError):
            self.svc.xoa_phong("B1")
        with self.assertRaises(PermissionError):
            self.svc.xoa_sinh_vien("SV4")

    def test_xac_thuc_theo_vai_tro(self):
        self.assertTrue(xac_thuc("admin", "admin123", "admin"))
        self.assertTrue(xac_thuc("sinhvien", "sv123456", "sinh_vien"))
        self.assertFalse(xac_thuc("admin", "admin123", "khach"))
        self.assertFalse(xac_thuc("admin", "sai", "admin"))

    def test_hoa_don_va_cong_no(self):
        self.svc.xep_phong("SV1", "A101")
        hd = self.svc.tao_hoa_don("A101", "2026-09", 100, 10)
        self.assertEqual(hd.tong_tien, 900_000 + 100 * 3500 + 10 * 15000)
        self.assertEqual(self.svc.cong_no(), hd.tong_tien)
        self.svc.danh_dau_da_thu(hd.ma_hoa_don)
        self.assertEqual(self.svc.cong_no(), 0)

    def test_hop_dong_sap_het_han(self):
        self.svc.xep_phong("SV1", "A101")
        self.svc.them_hop_dong(HopDong("HD1", "SV1", "A101", "2026-01-01", "2026-10-25"))
        ds = self.svc.hop_dong_sap_het_han(30, hom_nay=date(2026, 10, 17))
        self.assertEqual([h.ma_hd for h in ds], ["HD1"])

    def test_xoa_vi_pham(self):
        self.svc.them_vi_pham(ViPham("VP1", "SV1", "2026-10-17", "Nấu ăn trong phòng", 200_000))
        self.svc.xoa_vi_pham("VP1")
        self.assertNotIn("VP1", self.svc.vi_pham)

    def test_cap_nhat_sinh_vien_giu_nguyen_phong(self):
        self.svc.xep_phong("SV1", "A101")
        self.svc.cap_nhat_sinh_vien("SV1", SinhVien("SV1", "An mới", "Nam", "0912"))
        self.assertEqual(self.svc.sinh_vien["SV1"].ho_ten, "An mới")
        self.assertEqual(self.svc.sinh_vien["SV1"].ma_phong, "A101")

    def test_cap_nhat_hop_dong(self):
        self.svc.them_hop_dong(HopDong("HD1", "SV1", "A101", "2026-01-01", "2026-10-25"))
        self.svc.cap_nhat_hop_dong(
            "HD1", HopDong("HD1", "SV1", "A101", "2026-02-01", "2026-11-25", 500_000)
        )
        self.assertEqual(self.svc.hop_dong["HD1"].tien_coc, 500_000)

    def test_xoa_vi_pham_kiem_tra_quyen(self):
        self.svc.vai_tro = "khach"
        with self.assertRaises(PermissionError):
            self.svc.xoa_vi_pham("VP1")

    def test_luu_va_doc_lai(self):
        s = tao_du_lieu_mau(DormService("admin"))
        s2 = DormService.from_dict(s.to_dict())
        self.assertEqual(len(s2.phong), len(s.phong))
        self.assertEqual(len(s2.sinh_vien), len(s.sinh_vien))
        self.assertEqual(s2.cong_no(), s.cong_no())


if __name__ == "__main__":
    unittest.main()
