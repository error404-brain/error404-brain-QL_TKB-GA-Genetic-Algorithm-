from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from .models import GiangVien, LopHocPhan, TietHoc, ThoiKhoaBieu
from datetime import timedelta, date, datetime
from django.utils import timezone
import random
from .forms import CSVUploadForm
import csv
from .forms import ThoiKhoaBieuForm
from .utils import load_giang_vien_from_csv, load_mon_hoc_from_csv, load_phong_hoc_from_csv, load_lop_hoc_phan_from_csv, load_tiet_hoc_from_csv,writing_thoiKhoaBieu_csv
from django.db.models import Q

HOLIDAYS = [
    (1, 1),
    (2, 14),
    (3, 8),
    (4, 30),
    (5, 1),
]

def is_holiday(day):
    return (day.month, day.day) in HOLIDAYS

def find_next_available_day(day):
    while is_holiday(day):
        day += timedelta(days=1)
    return day

def create_individual():
    individual = []
    schedule = {}
    all_tiet_hoc = list(TietHoc.objects.all())
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for lop_hoc_phan in LopHocPhan.objects.all():
        if lop_hoc_phan.NgayKetThuc >= timezone.now().date():
            conflict_found = True
            attempt_count = 0  # Đếm số lần thử
            
            while conflict_found and attempt_count < len(days_of_week):
                tiet_hoc = random.choice(all_tiet_hoc)
                ngay_trong_tuan = random.choice(days_of_week)
                ngay_trong_tuan_date = timezone.now().date() + timedelta(days=(days_of_week.index(ngay_trong_tuan) - timezone.now().date().weekday()))
                ngay_trong_tuan_date = find_next_available_day(ngay_trong_tuan_date)
                
                key = (lop_hoc_phan.phong_hoc, tiet_hoc, ngay_trong_tuan_date)
                gv_key = (lop_hoc_phan.giang_vien, ngay_trong_tuan_date)

                if gv_key not in schedule:
                    schedule[gv_key] = []

                # Kiểm tra xung đột dựa trên thời gian thực tế (GioBatDau và GioKetThuc)
                conflict = False
                for scheduled_tiet_hoc in schedule[gv_key]:
                    if not (tiet_hoc.GioBatDau >= scheduled_tiet_hoc.GioKetThuc or tiet_hoc.GioKetThuc <= scheduled_tiet_hoc.GioBatDau):
                        conflict = True
                        break

                if key not in schedule and not conflict:
                    schedule[key] = lop_hoc_phan
                    schedule[gv_key].append(tiet_hoc)  # Thêm tiết học vào danh sách của giảng viên trong ngày
                    individual.append((lop_hoc_phan, tiet_hoc, ngay_trong_tuan_date))
                    conflict_found = False
                else:
                    # Nếu có xung đột, thử ngày khác
                    attempt_count += 1
                    next_day_index = (days_of_week.index(ngay_trong_tuan) + 1) % len(days_of_week)
                    ngay_trong_tuan = days_of_week[next_day_index]
                
                # Nếu đã thử hết các ngày trong tuần mà không tìm thấy ngày phù hợp
                if attempt_count >= len(days_of_week):
                    print(f"Không thể tìm thấy ngày phù hợp cho lớp {lop_hoc_phan} với tiết {tiet_hoc.TietTrongKhungGio}.")
                    conflict_found = False  # Ngăn chặn vòng lặp vô tận
                    break
    
    return individual

def fitness(individual):
    score = 0
    schedule = {}
    
    for lop_hoc_phan, tiet_hoc, ngay_trong_tuan in individual:
        key = (lop_hoc_phan.phong_hoc, tiet_hoc, ngay_trong_tuan)
        gv_key = (lop_hoc_phan.giang_vien, ngay_trong_tuan)
        mon_key = (lop_hoc_phan.mon_hoc, ngay_trong_tuan)
        
        # Kiểm tra xung đột về phòng học
        if key not in schedule:
            schedule[key] = lop_hoc_phan
            score += 1
        else:
            score -= 1
        
        # Kiểm tra xung đột về giảng viên
        if gv_key not in schedule:
            schedule[gv_key] = lop_hoc_phan
            score += 1
        else:
            score -= 1
        
        # Kiểm tra xung đột về môn học
        if mon_key not in schedule:
            schedule[mon_key] = lop_hoc_phan
            score += 1
        else:
            score -= 1
    
    return score


def selection(population):
    population.sort(key=lambda x: fitness(x), reverse=True)
    return population[:len(population)//2]

def crossover(parent1, parent2):
    index = random.randint(0, len(parent1)-1)
    child1 = parent1[:index] + parent2[index:]
    child2 = parent2[:index] + parent1[index:]
    return child1, child2

def mutate(individual, mutation_rate=0.01):
    if random.random() < mutation_rate:
        index = random.randint(0, len(individual) - 1)
        lop_hoc_phan, tiet_hoc, ngay_trong_tuan = individual[index]

        while True:
            tiet_hoc = random.choice(TietHoc.objects.all())
            ngay_trong_tuan = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            ngay_trong_tuan = timezone.now().date() + timedelta(days=(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(ngay_trong_tuan) - timezone.now().date().weekday()))
            ngay_trong_tuan = find_next_available_day(ngay_trong_tuan)
            key = (lop_hoc_phan.phong_hoc, tiet_hoc, ngay_trong_tuan)
            gv_key = (lop_hoc_phan.giang_vien, tiet_hoc, ngay_trong_tuan)

            if key not in [ind[:2] for ind in individual] and gv_key not in [ind[:2] for ind in individual]:
                individual[index] = (lop_hoc_phan, tiet_hoc, ngay_trong_tuan)
                break


def genetic_algorithm(generations=10, population_size=10):
    start_time = datetime.now()  # Thời gian bắt đầu
    population = [create_individual() for _ in range(population_size)]
    
    for generation in range(generations):
        population = selection(population)
        next_population = []
        while len(next_population) < population_size:
            parent1, parent2 = random.sample(population, 2)
            child1, child2 = crossover(parent1, parent2)
            mutate(child1)
            mutate(child2)
            next_population.extend([child1, child2])
        population = next_population

    best_individual = max(population, key=lambda x: fitness(x))
    end_time = datetime.now()  # Thời gian kết thúc

    duration = end_time - start_time  # Thời gian hoàn thành
    return best_individual, duration


def load_schedule_view(request):
    if request.method == 'POST':
        csv_file = request.FILES['file']
        csv_file1 = request.FILES['file_mon_hoc']
        csv_file2 = request.FILES['file_phong_hoc']
        csv_file3 = request.FILES['file_tiet_hoc']
        csv_file4 = request.FILES['file_lop_hoc_phan']
        LopHocPhan.objects.all().delete()
        ThoiKhoaBieu.objects.all().delete()

        load_giang_vien_from_csv(csv_file)
        load_mon_hoc_from_csv(csv_file1)
        load_phong_hoc_from_csv(csv_file2)
        load_tiet_hoc_from_csv(csv_file3)
        load_lop_hoc_phan_from_csv(csv_file4)

        start_time = datetime.now()  # Thời gian bắt đầu
        best_schedule, duration = genetic_algorithm()
        
        for lop_hoc_phan, tiet_hoc, ngay_trong_tuan in best_schedule:
            current_date = lop_hoc_phan.NgayBatDau
            while current_date <= lop_hoc_phan.NgayKetThuc:
                if current_date.strftime('%A') == ngay_trong_tuan.strftime('%A'):
                    current_date = find_next_available_day(current_date)
                    ThoiKhoaBieu.objects.create(
                        lop_hoc_phan=lop_hoc_phan,
                        thoi_gian=tiet_hoc,
                        ngay_trong_tuan=ngay_trong_tuan.strftime('%A'),
                        ngay_thuc_te=current_date
                    )
                current_date += timedelta(days=1)
        writing_thoiKhoaBieu_csv()
        end_time = datetime.now()  # Thời gian kết thúc

        # Tính thời gian hoàn thành
        time_taken = end_time - start_time
        minutes_taken = time_taken.total_seconds() / 60


        # Truyền thời gian hoàn thành đến template
        return render(request, 'pages/schedule_result.html', {
            'duration': duration,
            'time_taken_minutes': minutes_taken
        })
    else:
        return render(request, 'pages/schedule.html')




def show_tkb(request):
    timetable = ThoiKhoaBieu.objects.all()
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return render(request, 'pages/show_schedule.html', {'timetable': timetable, 'days_of_week': days_of_week})


def find_tkb_by_id(request):
    giang_vien_s = GiangVien.objects.all()
    giang_vien_id = request.GET.get('giang_vien_id')
    start_date_str = request.GET.get('start_date')
    next_week = request.GET.get('next_week', 'false') == 'true'
    prev_week = request.GET.get('prev_week','false') == 'true'
    
    if request.method == 'POST':
        giang_vien_id = request.POST.get('giang_vien_id')
        start_date_str = request.POST.get('start_date')
    
    if giang_vien_id:
        giang_vien = get_object_or_404(GiangVien, id=giang_vien_id)
        lop_hoc_phan_s = LopHocPhan.objects.filter(giang_vien=giang_vien)

        if not lop_hoc_phan_s.exists():
            return render(request, 'pages/find_TKB.html', {
                'giang_viens': giang_vien_s, 
                'error': 'Không có lớp học phần nào cho giảng viên này.'
            })
        
        if not start_date_str:
            start_date = lop_hoc_phan_s.earliest('NgayBatDau').NgayBatDau
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if next_week:
                start_date += timedelta(weeks=1)
            if prev_week:
                start_date -= timedelta(weeks=1)

        start_date_of_week = start_date - timedelta(days=start_date.weekday())
        days_of_week =  ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        days_of_weeks = {days_of_week[i]: start_date_of_week + timedelta(days=i) for i in range(7)}

        timetable = ThoiKhoaBieu.objects.filter(
            lop_hoc_phan__giang_vien=giang_vien,
            lop_hoc_phan__NgayBatDau__lte=start_date_of_week + timedelta(days=6),
            lop_hoc_phan__NgayKetThuc__gte=start_date_of_week
        )

        return render(request, 'pages/show_schedule.html', {
            'timetable': timetable,
            'days_of_weeks': days_of_weeks,
            'start_date_of_week': start_date_of_week,
            'giang_vien': giang_vien,
            'giang_vien_id': giang_vien_id,
            'start_date': start_date.strftime('%Y-%m-%d')
        })

    return render(request, 'pages/find_TKB.html', {'giang_viens': giang_vien_s})
    


def check_schedule_conflict(thoi_khoa_bieu):
    # Kiểm tra xung đột về phòng học
    phong_hoc_conflict = ThoiKhoaBieu.objects.filter(
        Q(thoi_gian=thoi_khoa_bieu.thoi_gian) &
        Q(ngay_trong_tuan=thoi_khoa_bieu.ngay_trong_tuan) &
        Q(lop_hoc_phan__phong_hoc=thoi_khoa_bieu.lop_hoc_phan.phong_hoc)& 
        Q(ngay_thuc_te=thoi_khoa_bieu.ngay_thuc_te)
    ).exclude(id=thoi_khoa_bieu.id).first()

    # Kiểm tra xung đột về giáo viên
    giang_vien_conflict = ThoiKhoaBieu.objects.filter(
        Q(thoi_gian=thoi_khoa_bieu.thoi_gian) &
        Q(ngay_trong_tuan=thoi_khoa_bieu.ngay_trong_tuan) &
        Q(lop_hoc_phan__giang_vien=thoi_khoa_bieu.lop_hoc_phan.giang_vien)& 
        Q(ngay_thuc_te=thoi_khoa_bieu.ngay_thuc_te)
    ).exclude(id=thoi_khoa_bieu.id).first()

    # Kiểm tra xung đột về lớp học
    lop_hoc_conflict = ThoiKhoaBieu.objects.filter(
        Q(thoi_gian=thoi_khoa_bieu.thoi_gian) &
        Q(ngay_trong_tuan=thoi_khoa_bieu.ngay_trong_tuan) &
        Q(lop_hoc_phan=thoi_khoa_bieu.lop_hoc_phan)&
        Q(ngay_thuc_te=thoi_khoa_bieu.ngay_thuc_te)
    ).exclude(id=thoi_khoa_bieu.id).first()

    if phong_hoc_conflict:
        return f'Phòng học "{phong_hoc_conflict.lop_hoc_phan.phong_hoc}" đã bị trùng vào thời gian {phong_hoc_conflict.thoi_gian} ngày {phong_hoc_conflict.ngay_trong_tuan}.'
    if giang_vien_conflict:
        return f'Giáo viên "{giang_vien_conflict.lop_hoc_phan.giang_vien}" đã bị trùng vào thời gian {giang_vien_conflict.thoi_gian} ngày {giang_vien_conflict.ngay_thuc_te}.'
    if lop_hoc_conflict:
        return f'Lớp học "{lop_hoc_conflict.lop_hoc_phan}" đã bị trùng vào thời gian {lop_hoc_conflict.thoi_gian} ngày {lop_hoc_conflict.ngay_trong_tuan}.'
    
    return None







def calculate_real_date(start_date, day_of_week):
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    # Ensure the start_date is the beginning of the week
    start_date_of_week = start_date - timedelta(days=start_date.weekday())
    # List of days of the week in the correct order
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Validate the input day_of_week
    if day_of_week not in days_of_week:
        raise ValueError(f"'{day_of_week}' is not a valid day of the week")
    # Calculate the exact date of the given day_of_week in the target week
    desired_date = start_date_of_week + timedelta(days=days_of_week.index(day_of_week))
    return desired_date





#ĐỔI TOÀN BỘ TẤT CẢ LICH HỌC THEO THỨ
def edit_schedule(request, thoi_khoa_bieu_id):
    thoi_khoa_bieu = get_object_or_404(ThoiKhoaBieu, id=thoi_khoa_bieu_id)

    # Xác định giá trị của start_date từ GET hoặc POST request
    start_date_str = request.GET.get('start_date') or request.POST.get('start_date')
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = thoi_khoa_bieu.lop_hoc_phan.NgayBatDau

    if request.method == 'POST':
        form = ThoiKhoaBieuForm(request.POST, instance=thoi_khoa_bieu)
        edit_choice = request.POST.get('edit_choice')
        new_date_str = request.POST.get('new_date')

        if form.is_valid():
            temp_thoi_khoa_bieu = form.save(commit=False)
            ngay_thuc_te_str = request.POST.get('ngay_thuc_te')
            if ngay_thuc_te_str:
                try:
                    temp_thoi_khoa_bieu.ngay_thuc_te = datetime.strptime(ngay_thuc_te_str, '%Y-%m-%d').date()
                except ValueError:
                    form.add_error('ngay_thuc_te', 'Ngày thực tế không hợp lệ')

            ngay_trong_tuan_str = request.POST.get('ngay_trong_tuan')
            if ngay_trong_tuan_str:
                try:
                    temp_thoi_khoa_bieu.ngay_trong_tuan = ngay_trong_tuan_str
                    temp_thoi_khoa_bieu.ngay_thuc_te = start_date + timedelta(days=(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(ngay_trong_tuan_str) - start_date.weekday()))
                except ValueError:
                    form.add_error('ngay_trong_tuan', 'Ngày trong tuần không hợp lệ')
            
            # Kiểm tra lựa chọn chỉnh sửa
            if edit_choice == 'day':
                pass  # Không thay đổi thông tin của lớp học phần hoặc thời gian
            elif edit_choice == 'week':
                # Thay đổi toàn bộ tuần (cập nhật thoi_gian và lop_hoc_phan)
                related_schedules = ThoiKhoaBieu.objects.filter(lop_hoc_phan=thoi_khoa_bieu.lop_hoc_phan)
                for schedule in related_schedules:
                    schedule.ngay_thuc_te = schedule.ngay_thuc_te + timedelta(days=(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(ngay_trong_tuan_str) - ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(schedule.ngay_trong_tuan)))
                    schedule.ngay_trong_tuan = ngay_trong_tuan_str
                    schedule.thoi_gian = temp_thoi_khoa_bieu.thoi_gian
                    schedule.save()

            conflict_error = check_schedule_conflict(temp_thoi_khoa_bieu)
            if conflict_error:
                form.add_error(None, conflict_error)
            else:
                temp_thoi_khoa_bieu.save()

                giang_vien_id = temp_thoi_khoa_bieu.lop_hoc_phan.giang_vien.id

                if new_date_str:
                    new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
                    temp_thoi_khoa_bieu.ngay_thuc_te = new_date
                    temp_thoi_khoa_bieu.ngay_trong_tuan = new_date.strftime('%A')
                    temp_thoi_khoa_bieu.save()
                    return HttpResponseRedirect(f'/find_tkb_by_id/?giang_vien_id={giang_vien_id}&start_date={start_date.strftime("%Y-%m-%d")}')

                return HttpResponseRedirect(f'/find_tkb_by_id/?giang_vien_id={giang_vien_id}&start_date={start_date.strftime("%Y-%m-%d")}')
    else:
        form = ThoiKhoaBieuForm(instance=thoi_khoa_bieu)

    try:
        ngay_thuc_te = calculate_real_date(start_date, thoi_khoa_bieu.ngay_trong_tuan)
    except ValueError as e:
        ngay_thuc_te = None
        form.add_error(None, str(e))

    return render(request, 'pages/edit_schedule.html', {
        'form': form,
        'ngay_trong_tuan': thoi_khoa_bieu.ngay_trong_tuan,
        'ngay_thuc_te': ngay_thuc_te.strftime('%Y-%m-%d') if ngay_thuc_te else '',
    })



def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            csv_file1 = request.FILES['file_mon_hoc']
            csv_file2 = request.FILES['file_phong_hoc']
            csv_file3 = request.FILES['file_tiet_hoc']
            csv_file4 = request.FILES['file_lop_hoc_phan']
            load_giang_vien_from_csv(csv_file)
            load_mon_hoc_from_csv(csv_file1)
            load_phong_hoc_from_csv(csv_file2)
            load_tiet_hoc_from_csv(csv_file3)
            load_lop_hoc_phan_from_csv(csv_file4)
            return redirect('load_schedule')
    else:
        form = CSVUploadForm()
    return render(request, 'pages/upload_csv.html', {'form': form})