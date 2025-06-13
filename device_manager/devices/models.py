# devices/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class DeviceType(models.Model):
    """设备大类型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="设备大类型")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '设备大分类表'
        verbose_name_plural = verbose_name


class Device(models.Model):
    """设备信息"""
    STATUS_CHOICES = (
        ('ok', '正常'),
        ('borrowed', '已借出'),
        ('maintenance', '维修中'),
        ('damaged', '已损坏'),
    )

    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, verbose_name="设备大类型")
    device_number = models.CharField(max_length=50, unique=True, verbose_name="设备编号")
    type = models.CharField(max_length=50, verbose_name="设备类型")
    brand = models.CharField(max_length=50, verbose_name="品牌")
    model = models.CharField(max_length=50, verbose_name="型号")
    details = models.TextField(blank=True, null=True, verbose_name="设备详细信息")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ok', verbose_name="当前状态")
    # 添加图片字段
    image = models.ImageField(upload_to='devices_images/', blank=True, null=True, verbose_name="设备图片",
                              default='images/default.jpg')

    def __str__(self):
        return f"{self.device_number} - {self.brand} {self.model}"

    class Meta:
        verbose_name = '设备总表'
        verbose_name_plural = verbose_name


class BorrowRecord(models.Model):
    """借用记录"""
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="借用人")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name="设备")
    borrow_date = models.DateTimeField(default=timezone.now, verbose_name="借用日期")
    estimated_return_date = models.DateTimeField(verbose_name="预估归还日期")
    actual_return_date = models.DateTimeField(null=True, blank=True, verbose_name="实际归还日期")

    # 新增字段，用于表示借用记录的当前状态
    STATUS_CHOICES = (
        ('unreturned', '未归还'),
        ('returned', '已归还'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unreturned', verbose_name="当前状态")

    def __str__(self):
        return f"{self.borrower.username} 借用 {self.device.device_number}；当前状态： {self.get_status_display()}"

    def is_overdue(self):
        """检查是否逾期"""
        return not self.actual_return_date and timezone.now() > self.estimated_return_date

    class Meta:
        verbose_name = '设备借用记录表'
        verbose_name_plural = verbose_name


class DeviceIssue(models.Model):
    """设备异常记录"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name="设备")
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="上报人")
    description = models.TextField(verbose_name="异常描述")
    report_date = models.DateTimeField(default=timezone.now, verbose_name="上报日期")
    is_handled = models.BooleanField(default=False, verbose_name="是否处理")
    handled_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="handled_issues", verbose_name="处理人")
    handle_result = models.TextField(null=True, blank=True, verbose_name="处理结果")
    handle_date = models.DateTimeField(null=True, blank=True, verbose_name="处理日期")


    # 是否处理进行在处理,由于是Boolean需要自定义或者修改
    is_handled_CHOICES = (
        ('True', '是'),
        ('False', '否'),
    )
    # 自定义 get_is_handled_display 方法
    def get_is_handled_display(self):
        for value, text in self.is_handled_CHOICES:
            if str(self.is_handled) == value:
                return text
        return

    def __str__(self):
        return f"{self.device.device_number} 的异常上报---已处理状态: {self.get_is_handled_display()} "

    class Meta:
        verbose_name = '设备异常记录表'
        verbose_name_plural = verbose_name
