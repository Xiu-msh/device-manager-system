# devices/forms.py
from django import forms
from django.contrib.auth.forms import authenticate, UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Device, BorrowRecord, DeviceIssue, DeviceType
from django.utils import timezone


class UserRegistrationForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserLoginForm(AuthenticationForm):
    """用户登录表单"""
    """此处有问题，后端验证表单出问题,当前在views直接通过AuthenticationForm验证"""
    username = forms.CharField(label='用户名')
    password = forms.CharField(label='密码', widget=forms.PasswordInput)


class DeviceQueryForm(forms.Form):
    """设备查询表单"""
    device_type = forms.ModelChoiceField(
        queryset=DeviceType.objects.all(),
        empty_label="所有设备类型",
        required=False  # 允许不选择设备类型
    )

    STATUS_CHOICES = (
        ('', '所有状态'),  # 空字符串表示所有状态
        ('ok', '正常'),
        ('borrowed', '已借出'),
        ('maintenance', '维修中'),
        ('damaged', '已损坏'),
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False  # 允许不选择状态
    )

    type = forms.CharField(
        max_length=50,
        required=False,
        label="设备类型",
        widget=forms.TextInput(attrs={'placeholder': '输入设备类型'})
    )


class BorrowForm(forms.ModelForm):
    """借用设备表单"""

    class Meta:
        model = BorrowRecord
        fields = ['estimated_return_date']
        widgets = {
            'estimated_return_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'custom-datetime-input',  # 添加自定义 CSS 类
                    'required': True
                }
            ),
        }

    def clean_estimated_return_date(self):
        estimated_return_date = self.cleaned_data.get('estimated_return_date')
        if estimated_return_date and estimated_return_date < timezone.now():
            raise forms.ValidationError("预计归还日期不能低于当前时间。")
        return estimated_return_date


class ReturnForm(forms.Form):
    """归还设备表单"""
    confirmation = forms.BooleanField(
        required=True,
        label='我确认归还该设备',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    issue_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='设备异常描述（如果有）'
    )


class DeviceIssueForm(forms.ModelForm):
    """设备异常上报表单"""

    class Meta:
        model = DeviceIssue
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
