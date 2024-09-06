from django import forms
from .models import GiangVien,MonHoc,PhongHoc,TietHoc,LopHocPhan,ThoiKhoaBieu


class LopHocPhanForm(forms.ModelForm):
    class Meta:
        model = LopHocPhan
        fields = ['mon_hoc','giang_vien','phong_hoc','SiSo']
    def save(self,commit = True):
        lop_hoc_phan = super().save(commit= False)
        if commit:
            lop_hoc_phan.save()
        return lop_hoc_phan
        
DAYS_OF_WEEK = [
    ('Monday', 'Thứ Hai'),
    ('Tuesday', 'Thứ Ba'),
    ('Wednesday', 'Thứ Tư'),
    ('Thursday', 'Thứ Năm'),
    ('Friday', 'Thứ Sáu'),
    ('Saturday', 'Thứ Bảy'),
    ('Sunday', 'Chủ Nhật'),
]



class ThoiKhoaBieuForm(forms.ModelForm):
    ngay_trong_tuan = forms.ChoiceField(
        choices=DAYS_OF_WEEK,
    )

    class Meta:
        model = ThoiKhoaBieu
        fields = ['lop_hoc_phan', 'ngay_trong_tuan', 'thoi_gian', 'ngay_thuc_te']  # Thêm trường ngay_thuc_te
    
    def save(self, commit=True):
        thoi_khoa_bieu = super().save(commit=False)
        thoi_khoa_bieu.ngay_trong_tuan = self.cleaned_data['ngay_trong_tuan']
        if commit:
            thoi_khoa_bieu.save()
        return thoi_khoa_bieu

class CSVUploadForm(forms.Form):
    file = forms.FileField()
    file_mon_hoc=forms.FileField()
    file_phong_hoc = forms.FileField()
    file_tiet_hoc=forms.FileField()
    file_lop_hoc_phan=forms.FileField()