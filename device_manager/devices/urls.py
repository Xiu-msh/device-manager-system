# devices/urls.py

from django.urls import path
from .views import (
    home, user_register, user_login, user_logout,
    device_query, device_borrow, device_return, device_issue_report, device_detail
)

urlpatterns = [
    path('', home, name='home'),
    path('register/', user_register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    path('device/query/', device_query, name='device_query'),
    path('device/borrow/<int:device_id>/', device_borrow, name='device_borrow'),
    path('device/return/<int:record_id>/', device_return, name='device_return'),
    path('device/issue/report/<int:device_id>/', device_issue_report, name='device_issue_report'),
    path('device/detail/<int:device_id>/', device_detail, name='device_detail'),
]
