from django.urls import path
from . import views

urlpatterns = [
    path('load_schedule/', views.load_schedule_view, name='load_schedule'),
    path('schedule/', views.show_tkb, name='show_tkb'),
    path('find_tkb_by_id/', views.find_tkb_by_id, name='find_tkb_by_id'),
    path('edit_schedule/<int:thoi_khoa_bieu_id>', views.edit_schedule, name='edit_schedule'),
    path('', views.upload_csv, name='upload_csv'),

]
