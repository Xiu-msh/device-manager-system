# device_manager/devices/admin.py

from django.contrib import admin
from .models import DeviceType, Device, BorrowRecord, DeviceIssue
from django.http import HttpResponse
from django.utils.timezone import is_aware, make_naive
from openpyxl.styles import NamedStyle
import csv
import json
import io
import pandas as pd

admin.site.site_header = '设备管理系统后台'  # 设置header
admin.site.site_title = '设备管理系统后台'  # 设置title
admin.site.index_title = '设备管理系统后台'


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_filter = ('name',)  # 按设备大类型名称筛选
    actions = ['export_selected_device_types']

    # 写入CSV文件
    # def export_selected_device_types(self, request, queryset):
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename="device_types.csv"'
    #     writer = csv.writer(response)
    #     writer.writerow(['ID', '设备大类型'])
    #     for device_type in queryset:
    #         writer.writerow([device_type.id, device_type.name])
    #     return response

    # 写入xlsx文件
    def export_selected_device_types(self, request, queryset):
        # 将 QuerySet 转换为列表，并指定列名
        data = [{"数据库ID": item.id, "设备分类": item.name} for item in queryset]

        # 创建 DataFrame 并设置列名
        df = pd.DataFrame(data)
        # df = pd.DataFrame(data, columns=["大类ID", "value"])  # 确保列名为 id 和 name

        # 将数据写入内存中的 Excel 文件
        output = io.BytesIO()  # 创建一个内存中的二进制流
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="设备大类型", index=False)  # 写入表头

        # 准备 HTTP 响应
        response = HttpResponse(
            output.getvalue(),  # 获取内存中的数据
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=device_types.xlsx'  # 设置文件名
        return response

    export_selected_device_types.short_description = "导出选中的设备大类型"


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_filter = ('device_type', 'type', 'brand', 'model', 'status',)
    actions = ['export_selected_devices']

    def export_selected_devices(self, request, queryset):
        # 创建一个字典用于存储不同 device_type.name 的数据
        data_by_device_type = {}

        # 遍历查询集，按 device_type.name 分组数据
        for device in queryset:
            device_type_name = device.device_type.name if device.device_type else '未分类'

            if device_type_name not in data_by_device_type:
                data_by_device_type[device_type_name] = []  # 如果设备类型尚未存在，创建一个新的列表

            # 构建当前设备的数据行
            row = {
                '数据库ID': device.id,
                '设备大类型名称': device.device_type.name if device.device_type else '',
                '设备编号': device.device_number,
                '设备类型': device.type,
                '品牌': device.brand,
                '型号': device.model,
                '状态': device.get_status_display(),
            }

            # 将device.details通过update到row中
            try:
                # 解析 details 字段为字典
                device_details = json.loads(device.details) if device.details else {}
                if isinstance(device_details, dict):
                    row.update(device_details)  # 将详细信息字段添加到数据行
            except json.JSONDecodeError:
                pass  # 忽略解析失败的情况

            # 将当前设备的数据行添加到对应 device_type.name 的列表中
            data_by_device_type[device_type_name].append(row)

        # 创建一个 Excel 写入器
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for device_type_name, data_list in data_by_device_type.items():
                # 将数据转换为 DataFrame
                df = pd.DataFrame(data_list)
                # 将数据写入对应的 sheet 中，sheet 名为设备大类型名称
                df.to_excel(writer, sheet_name=device_type_name, index=False)  # sheet 名长度限制为 31 个字符

        # 准备 HTTP 响应
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=devices.xlsx'  # 设置文件名
        return response

    export_selected_devices.short_description = "导出选中的设备信息"

    # 写入CSV文件
    # def export_selected_devices(self, request, queryset):
    #     # 动态获取所有可能的详细信息字段
    #     all_details_keys = set()
    #     for device in queryset:
    #         try:
    #             # 使用 json.loads 将 JSON 字符串转换为字典
    #             device_details = json.loads(device.details) if device.details else {}
    #             if isinstance(device_details, dict):
    #                 all_details_keys.update(device_details.keys())
    #         except json.JSONDecodeError:
    #             # 如果解析失败，忽略该设备的详细信息
    #             continue
    #
    #     # 将详细信息字段按顺序排列
    #     details_keys = sorted(all_details_keys)
    #
    #     # 构建 CSV 响应
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename="devices.csv"'
    #     writer = csv.writer(response)
    #
    #     # 写入表头
    #     # header = ['ID', '设备大类型', '设备编号', '设备类型', '品牌', '型号', '状态']
    #     header = ['设备大类型', '设备编号', '设备类型', '品牌', '型号', '状态']
    #     header.extend(details_keys)  # 添加详细信息字段
    #     header.append('图片')
    #     writer.writerow(header)
    #
    #     # 写入数据行
    #     for device in queryset:
    #         row = [
    #             # device.id,
    #             device.device_type.name,
    #             device.device_number,
    #             device.type,
    #             device.brand,
    #             device.model,
    #             device.get_status_display(),
    #         ]
    #
    #         try:
    #             # 使用 json.loads 将 JSON 字符串转换为字典
    #             device_details = json.loads(device.details) if device.details else {}
    #             if isinstance(device_details, dict):
    #                 for key in details_keys:
    #                     row.append(device_details.get(key, ''))  # 如果键不存在，填充为空字符串
    #             else:
    #                 row.extend([''] * len(details_keys))  # 如果不是字典，填充空列
    #         except json.JSONDecodeError:
    #             row.extend([''] * len(details_keys))  # 如果解析失败，填充空列
    #
    #         # 添加图片字段
    #         row.append(device.image)
    #
    #         writer.writerow(row)
    #     return response


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_filter = ('borrower', 'status',)  # 按借用人、归还状态筛选
    actions = ['export_selected_borrow_records']

    # 写入xlsx文件
    def export_selected_borrow_records(self, request, queryset):
        # 将 QuerySet 转换为列表，并指定列名
        # 不能含有带时间时区的格式，需要去掉
        data = [
            {"数据库ID": item.id,
             '借用人': item.borrower.username,
             '设备': item.device.device_number,
             '借用日期': self.remove_tz(item.borrow_date),
             '预估归还日期': self.remove_tz(item.estimated_return_date),
             '实际归还日期': self.remove_tz(item.actual_return_date),
             '是否已归还': item.get_status_display(),
             }
            for item in queryset]

        # 创建 DataFrame 并设置列名
        df = pd.DataFrame(data)
        # df = pd.DataFrame(data,
        #                   columns=['数据库ID', '借用人', '设备', '借用日期', '预估归还日期', '实际归还日期', '是否已归还'])

        # 将数据写入内存中的 Excel 文件
        output = io.BytesIO()  # 创建一个内存中的二进制流
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="设备借用记录表", index=False)  # 写入表头

            # 获取工作表对象
            worksheet = writer.sheets["设备借用记录表"]

            # 定义日期格式样式
            date_style = NamedStyle(name='datetime', number_format='yyyy-mm-dd hh:mm:ss')

            # 设置列格式
            worksheet.column_dimensions['D'].width = 40  # 借用日期
            worksheet.column_dimensions['E'].width = 40  # 预估归还日期
            worksheet.column_dimensions['F'].width = 40  # 实际归还日期

            # 将样式应用到相应列
            for cell in worksheet['D']:
                cell.style = date_style
            for cell in worksheet['E']:
                cell.style = date_style
            for cell in worksheet['F']:
                cell.style = date_style

        # 准备 HTTP 响应
        response = HttpResponse(
            output.getvalue(),  # 获取内存中的数据
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=borrow_records.xlsx'  # 设置文件名

        return response

    # 写入CSV文件
    # def export_selected_borrow_records(self, request, queryset):
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename="borrow_records.csv"'
    #     writer = csv.writer(response)
    #     writer.writerow(['ID', '借用人', '设备', '借用日期', '预估归还日期', '实际归还日期', '是否已归还'])
    #     for record in queryset:
    #         writer.writerow([record.id, record.borrower.username, record.device.device_number, record.borrow_date,
    #                          record.estimated_return_date, record.actual_return_date, record.status])
    #     return response

    export_selected_borrow_records.short_description = "导出选中的设备大类型"

    @staticmethod
    def remove_tz(dt):
        """移除日期时间的时区信息"""
        if dt and is_aware(dt):
            return make_naive(dt)
        return dt


@admin.register(DeviceIssue)
class DeviceIssueAdmin(admin.ModelAdmin):
    list_filter = ('device', 'reporter', 'report_date', 'is_handled')  # 按设备、上报人、上报日期、是否处理筛选
    actions = ['export_selected_device_issues']

    # # 写入CSV文件
    # def export_selected_device_issues(self, request, queryset):
    #     response = HttpResponse(content_type='text/csv')
    #     response['Content-Disposition'] = 'attachment; filename="device_issues.csv"'
    #     writer = csv.writer(response)
    #     writer.writerow(['ID', '设备', '上报人', '异常描述', '上报日期', '是否处理', '处理人', '处理结果', '处理日期'])
    #     for issue in queryset:
    #         writer.writerow(
    #             [issue.id, issue.device.device_number, issue.reporter.username, issue.description, issue.report_date,
    #              issue.is_handled, issue.handled_by.username if issue.handled_by else '', issue.handle_result,
    #              issue.handle_date])
    #     return response

    # 写入xlsx文件
    def export_selected_device_issues(self, request, queryset):
        # 将 QuerySet 转换为列表，并指定列名
        # 不能含有带时间时区的格式，需要去掉
        #
        data = [
            {"数据库ID": item.id,
             '设备': item.device.device_number,
             '上报人': item.reporter.username,
             '异常描述':item.description,
             '上报日期': self.remove_tz(item.report_date),
             '是否处理': item.get_is_handled_display(),
             '处理人':  item.handled_by.username if item.handled_by else '',
             '处理结果': item.handle_result,
             '处理日期': self.remove_tz(item.handle_date)
             }
            for item in queryset]

        # 创建 DataFrame 并设置列名
        df = pd.DataFrame(data)
        # df = pd.DataFrame(data,
        #                   columns=['数据库ID', '设备', '上报人', '异常描述', '上报日期', '是否处理', '处理人', '处理结果', '处理日期'])

        # 将数据写入内存中的 Excel 文件
        output = io.BytesIO()  # 创建一个内存中的二进制流
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="设备借用记录表", index=False)  # 写入表头

            # 获取工作表对象
            worksheet = writer.sheets["设备借用记录表"]

            # 定义日期格式样式
            date_style = NamedStyle(name='datetime', number_format='yyyy-mm-dd hh:mm:ss')

            # 设置列格式
            worksheet.column_dimensions['E'].width = 40  # 上报日期
            worksheet.column_dimensions['I'].width = 40  # 处理日期


            # 将样式应用到相应列
            for cell in worksheet['E']:
                cell.style = date_style
            for cell in worksheet['I']:
                cell.style = date_style

        # 准备 HTTP 响应
        response = HttpResponse(
            output.getvalue(),  # 获取内存中的数据
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=device_issues.xlsx'  # 设置文件名

        return response

    export_selected_device_issues.short_description = "导出选中的设备异常记录"

    @staticmethod
    def remove_tz(dt):
        """移除日期时间的时区信息"""
        if dt and is_aware(dt):
            return make_naive(dt)
        return dt
