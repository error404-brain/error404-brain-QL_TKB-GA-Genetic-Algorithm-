from django.db import models

class GiangVien(models.Model):
    TenGiangVien = models.CharField(max_length=100)
    Email = models.CharField(max_length=100)
    SoDienThoai = models.CharField(max_length=10)
    DiaChi = models.CharField(max_length=100)

    def __str__(self):
        return self.TenGiangVien

class MonHoc(models.Model):
    TenMonHoc = models.CharField(max_length=100)
    SoTinhChi = models.IntegerField()
    LoaiMonHoc = models.CharField(max_length=20)

    def __str__(self):
        return self.TenMonHoc

class PhongHoc(models.Model):
    TenPhongHoc = models.CharField(max_length=20)
    SucChua = models.IntegerField()

    def __str__(self):
        return self.TenPhongHoc

class LopHocPhan(models.Model):
    mon_hoc = models.ForeignKey(MonHoc, on_delete=models.CASCADE)
    giang_vien = models.ForeignKey(GiangVien, on_delete=models.CASCADE)
    phong_hoc = models.ForeignKey(PhongHoc, on_delete=models.CASCADE)
    SiSo = models.IntegerField()
    NgayBatDau = models.DateField()
    NgayKetThuc = models.DateField()

    def __str__(self):
        return f"{self.mon_hoc} - {self.giang_vien}"

class TietHoc(models.Model):
    TietTrongKhungGio = models.CharField(max_length=50)
    GioBatDau = models.TimeField()
    GioKetThuc = models.TimeField()

    def __str__(self):
        return self.TietTrongKhungGio

class ThoiKhoaBieu(models.Model):
    lop_hoc_phan = models.ForeignKey(LopHocPhan, on_delete=models.CASCADE)
    thoi_gian = models.ForeignKey(TietHoc, on_delete=models.CASCADE)
    ngay_trong_tuan = models.CharField(max_length=10)
    ngay_thuc_te = models.DateField(null=True, blank=True)  # Thêm trường này

    def __str__(self):
        return f"{self.lop_hoc_phan} - {self.thoi_gian} - {self.ngay_trong_tuan} -{self.ngay_thuc_te}"
