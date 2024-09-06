import csv
from .models import GiangVien, MonHoc, PhongHoc, LopHocPhan, TietHoc, ThoiKhoaBieu

import os

# Base directory where CSV files are located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_giang_vien_from_csv(file):
    # Đọc dữ liệu từ tệp tải lên
    reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in reader:
        GiangVien.objects.update_or_create(
            TenGiangVien=row['TenGiangVien'],
            defaults={
                'Email': row['Email'],
                'SoDienThoai': row['SoDienThoai'],
                'DiaChi': row['DiaChi']
            }
        )

def load_mon_hoc_from_csv(file):
    reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in reader:
        MonHoc.objects.update_or_create(
            TenMonHoc=row['TenMonHoc'],
            defaults={
                'SoTinhChi': row['SoTinhChi'],
                'LoaiMonHoc': row['LoaiMonHoc']
            }
        )

def load_phong_hoc_from_csv(file):
    reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in reader:
        PhongHoc.objects.update_or_create(
            TenPhongHoc=row['TenPhongHoc'],
            defaults={
                'SucChua': row['SucChua']
            }
        )

def load_lop_hoc_phan_from_csv(file):
    reader = csv.DictReader(file.read().decode('utf-8').splitlines())

    for row in reader:
        mon_hoc_id = int(row['mon_hoc_id'])
        giang_vien_id = int(row['giang_vien_id'])
        phong_hoc_id = int(row['phong_hoc_id'])

        LopHocPhan.objects.update_or_create(
            mon_hoc_id=mon_hoc_id,
            giang_vien_id=giang_vien_id,
            phong_hoc_id=phong_hoc_id,
            defaults={
                'SiSo': row['SiSo'],
                'NgayBatDau': row['NgayBatDau'],
                'NgayKetThuc': row['NgayKetThuc']
            }
        )

def load_tiet_hoc_from_csv(file):
    reader = csv.DictReader(file.read().decode('utf-8').splitlines())
    for row in reader:
        TietHoc.objects.update_or_create(
            TietTrongKhungGio=row['TietTrongKhungGio'],
            defaults={
                'GioBatDau': row['GioBatDau'],
                'GioKetThuc': row['GioKetThuc']
            }
        )
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def writing_thoiKhoaBieu_csv():
    fieldnames = ['LopHocPhan', 'ThoiGian', 'NgayTrongTuan','NgayThucTe']
    relative_path = os.path.join(BASE_DIR, 'TKB_APP', 'CSV', 'thoiKhoaBieu.csv')
    with open(relative_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        thoi_khoa_bieu_list = ThoiKhoaBieu.objects.all()
        for tkb in thoi_khoa_bieu_list:
            writer.writerow({
                'LopHocPhan': str(tkb.lop_hoc_phan),
                'ThoiGian': str(tkb.thoi_gian),
                'NgayTrongTuan': tkb.ngay_trong_tuan,
                'NgayThucTe': tkb.ngay_thuc_te.strftime('%Y-%m-%d')
            })
         

# def check_schedule_conflict(thoi_khoa_bieu):
#     existing_entries = ThoiKhoaBieu.objects.filter(
#         thoi_gian=thoi_khoa_bieu.thoi_gian,
#         ngay_trong_tuan=thoi_khoa_bieu.ngay_trong_tuan
#     ).exclude(id=thoi_khoa_bieu.id)
#     return existing_entries.exists()
