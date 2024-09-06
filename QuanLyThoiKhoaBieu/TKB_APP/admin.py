from django.contrib import admin

# Register your models here.
from .models import GiangVien, MonHoc, PhongHoc, LopHocPhan, TietHoc, ThoiKhoaBieu

admin.site.register(GiangVien)
admin.site.register(MonHoc)
admin.site.register(PhongHoc)
admin.site.register(LopHocPhan)
admin.site.register(TietHoc)
admin.site.register(ThoiKhoaBieu)