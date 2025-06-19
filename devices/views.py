# devices/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import User, Device, DeviceType, BorrowRecord, DeviceIssue
from .forms import (UserRegistrationForm, UserLoginForm, DeviceQueryForm,
                    BorrowForm, ReturnForm, DeviceIssueForm)
from django.templatetags.static import static
import json
import os
from django.utils.http import url_has_allowed_host_and_scheme


def home(request):
    """主页视图"""
    if request.user.is_authenticated:
        borrow_records = BorrowRecord.objects.filter(
            borrower=request.user,
            actual_return_date__isnull=True
        ).select_related('device')
        return render(request, 'home.html', {'borrow_records': borrow_records})
    else:
        return redirect('login')


def user_register(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！已自动登录。')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def user_login(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, '登录成功！')
            return redirect('home')
        else:
            messages.error(request, form.errors.get('__all__', ['登录失败，请检查用户名和密码。'])[0])
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


@login_required
def user_logout(request):
    """用户注销视图"""
    logout(request)
    messages.success(request, '已成功退出登录！')
    return redirect('login')


@login_required
def device_query(request):
    """设备查询视图"""
    # 获取当前筛选条件，包括分页参数
    form_data = request.GET.copy()

    # 初始化表单并传递初始数据
    form = DeviceQueryForm(form_data)

    # 初始查询集
    devices = Device.objects.all()

    # 如果表单有效，则应用筛选条件
    if form.is_valid():
        device_type = form.cleaned_data.get('device_type')
        status = form.cleaned_data.get('status')
        type_text = form.cleaned_data.get('type')

        if device_type:
            devices = devices.filter(device_type=device_type)

        if status:
            devices = devices.filter(status=status)

        if type_text:
            devices = devices.filter(type__icontains=type_text)

    # 对查询集进行排序，这里以设备编号为例进行升序排序
    devices = devices.order_by('id')

    # 关联借用信息表(位于查询集顺序处理之后)
    devices = devices.prefetch_related('borrowrecord_set')
    for device in devices:
        try:
            device.latest_borrow_record = device.borrowrecord_set.latest('borrow_date')
            # # print(f"Device {device.id}: Latest borrow record - {device.latest_borrow_record}")
            # if device.latest_borrow_record:
            #     # print(f"  Borrower: {device.latest_borrow_record.borrower.username}")
            #     # print(f"  Borrow date: {device.latest_borrow_record.borrow_date}")
            #     # print(f"  Estimated return date: {device.latest_borrow_record.estimated_return_date}")
        except BorrowRecord.DoesNotExist:
            device.latest_borrow_record = None
            # print(f"Device {device.id}: No borrow records found.")

    # 分页处理
    paginator = Paginator(devices, 10)  # 每页显示10条记录
    page_number = request.GET.get('page', 1)  # 默认显示第一页
    page_obj = paginator.get_page(page_number)

    # 构建保留当前筛选条件的查询字符串（不包含page参数）
    query_string = request.GET.copy()
    if 'page' in query_string:
        del query_string['page']
    filtered_query_string = query_string.urlencode()

    return render(request, 'device_query.html', {
        'form': form,
        'page_obj': page_obj,
        'filtered_query_string': filtered_query_string,  # 传递过滤后的查询字符串
    })


@login_required
def device_detail(request, device_id):
    """设备详情视图"""
    device = get_object_or_404(Device, id=device_id)
    try:
        details = json.loads(device.details) if device.details else {}
    except json.JSONDecodeError:
        details = {}

    # 检查上传的图片是否存在
    if device.image and os.path.exists(device.image.path):
        image_path = device.image.url
    else:
        # 不存在使用静态文件
        image_path = static('images/default.jpg')

    device_info = {
        'device_id': device_id,

        'device_type': {
            'value': device.device_type.name,
            'verbose_name': Device._meta.get_field('device_type').verbose_name
        },
        'device_sub_type': {
            'value': device.type,
            'verbose_name': Device._meta.get_field('type').verbose_name
        },
        'device_number': {
            'value': device.device_number,
            'verbose_name': Device._meta.get_field('device_number').verbose_name
        },
        'brand': {
            'value': device.brand,
            'verbose_name': Device._meta.get_field('brand').verbose_name
        },
        'model': {
            'value': device.model,
            'verbose_name': Device._meta.get_field('model').verbose_name
        },
        'status': {
            'value': device.get_status_display(),
            'verbose_name': Device._meta.get_field('status').verbose_name
        },
        'details': details,
        'image': {
            'value': image_path,
            'verbose_name': Device._meta.get_field('image').verbose_name
        }
    }

    return render(request, 'device_detail.html', {'device_info': device_info})


@login_required
def device_borrow(request, device_id):
    """设备借用视图"""
    device = get_object_or_404(Device, id=device_id)
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            borrow_record = form.save(commit=False)
            borrow_record.borrower = request.user
            borrow_record.device = device
            borrow_record.status = 'unreturned'  # 设置为未归还
            borrow_record.save()

            device.status = 'borrowed'
            device.save()

            messages.success(request, '设备借用成功！')
            return redirect('device_query')
        else:
            messages.error(request, "表单输入有误，请检查。")  # 添加错误提示
    else:
        form = BorrowForm()

    return render(request, 'device_borrow.html', {'form': form, 'device': device})


# devices/views.py
@login_required
def device_return(request, record_id):
    """归还设备视图"""
    try:
        # 获取当前用户未归还的借用记录
        record = get_object_or_404(
            BorrowRecord,
            id=record_id,
            borrower=request.user,
            actual_return_date__isnull=True
        )
    except BorrowRecord.DoesNotExist:
        messages.error(request, "未找到对应的借用记录，请检查。")
        return redirect('home')
    except Exception as e:
        messages.error(request, f"获取借用记录时出错: {str(e)}")
        return redirect('home')

    if request.method == 'POST':
        form = ReturnForm(request.POST)
        has_issue = request.POST.get('has_issue')
        if form.is_valid():
            try:
                # 更新借用记录的实际归还日期和状态
                record.actual_return_date = timezone.now()
                record.status = 'returned'
                record.save()

                device = record.device
                issue_description = form.cleaned_data.get('issue_description')

                if has_issue == 'yes' and issue_description:
                    # 处理设备异常描述，创建一个新的 DeviceIssue 记录
                    issue = DeviceIssue.objects.create(
                        device=device,
                        reporter=request.user,
                        description=issue_description
                    )
                    # 将设备状态设置为维修中
                    device.status = 'maintenance'
                    device.save()
                    messages.success(request, '设备归还成功，异常已上报！')
                else:
                    # 设备正常，将设备状态设置为正常;如果当前设备已被上报异常，不做处理
                    if device.status != 'maintenance':
                        device.status = 'ok'
                        device.save()
                        messages.success(request, '设备归还成功！')

                return redirect('home')
            except Exception as e:
                messages.error(request, f"归还设备时出错: {str(e)}")
        else:
            messages.error(request, "表单输入有误，请检查。")
    else:
        form = ReturnForm()

    return render(request, 'device_return.html', {'form': form, 'record': record})


@login_required
def device_issue_report(request, device_id):
    """设备异常上报视图"""
    try:
        # 获取指定 ID 的设备
        device = get_object_or_404(Device, id=device_id)
    except Exception as e:
        messages.error(request, f"获取设备信息时出错: {str(e)}")
        return redirect('home')

    if request.method == 'POST':
        form = DeviceIssueForm(request.POST)
        if form.is_valid():
            try:
                # 创建设备异常记录
                issue = form.save(commit=False)
                issue.device = device
                issue.reporter = request.user
                issue.save()

                # 更新设备状态为维修中;
                device.status = 'maintenance'
                device.save()

                messages.success(request, '设备异常已上报！')
                return redirect('home')
            except Exception as e:
                messages.error(request, f"上报设备异常时出错: {str(e)}")
        else:
            messages.error(request, "表单输入有误，请检查。")
    else:
        form = DeviceIssueForm()

    return render(request, 'device_issue_report.html', {'form': form, 'device': device})
