import pandas as pd
import mysql.connector
import json
import os


# 检查Excel文件是否存在
def check_excel_file(file_path):
    if not os.path.exists(file_path):
        print(f"错误: Excel文件 '{file_path}' 不存在!")
        return False
    return True


# 转换DataFrame为适合数据库插入的格式
def dataframe_to_db_format(df):
    records = []
    exclude_columns = ['设备编号', '设备类型', '品牌', '型号', '状态']
    select_columns = [col for col in df.columns if col not in exclude_columns]

    for _, row in df.iterrows():
        if pd.notna(row['设备编号']):
            device_number = row['设备编号']
            type_ = row['设备类型']
            brand = row['品牌']
            model = row['型号']
            status = row['状态']

            details_values = row[select_columns]
            details = dict(zip(select_columns, details_values))

            # 处理缺失值和Timestamp对象
            for key, value in details.items():
                if pd.isna(value):
                    details[key] = None
                elif isinstance(value, pd.Timestamp):
                    details[key] = value.strftime('%Y-%m-%d %H:%M:%S')

            record = {
                'device_number': device_number,
                'type': type_,
                'brand': brand,
                'model': model,
                'status': status,
                'details': json.dumps(details, ensure_ascii=False),
            }
            records.append(record)

    return records


if __name__ == '__main__':
    # 数据库配置
    config = {
        'user': 'root',
        'password': '123456',
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'mydata',
        'raise_on_warnings': True
    }

    excel_file_path = 'device.xlsx'

    if not check_excel_file(excel_file_path):
        exit(1)

    conn = None
    try:
        # 创建MySQL数据库连接
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 读取Excel文件
        excel_file = pd.ExcelFile(excel_file_path)

        # 插入工作表名称到devices_devicetype表 - 存在则忽略，不存在则插入
        for sheet_name in excel_file.sheet_names:
            print(f"处理工作表: {sheet_name}")

            try:
                # 使用INSERT ... ON DUPLICATE KEY UPDATE实现存在则忽略，不存在则插入
                cursor.execute(
                    """
                    INSERT INTO `devices_devicetype` (name) 
                    VALUES (%s)
                    ON DUPLICATE KEY UPDATE name = name
                    """,
                    (sheet_name,)
                )
                conn.commit()

                # 检查执行结果
                cursor.execute('SELECT ROW_COUNT()')
                rows_affected = cursor.fetchone()[0]

                if rows_affected == 0:
                    print(f"  提示: 工作表 '{sheet_name}' 已存在，跳过插入")
                else:
                    print(f"  成功插入工作表: {sheet_name}")

            except mysql.connector.Error as e:
                conn.rollback()
                print(f"  插入工作表时出错: {e}")
                continue

            # 获取插入的工作表名称的ID
            cursor.execute('SELECT id FROM `devices_devicetype` WHERE name = %s', (sheet_name,))
            sheet_id_result = cursor.fetchone()
            if sheet_id_result:
                sheet_id = sheet_id_result[0]
            else:
                print(f"警告: 未找到工作表名称的ID: {sheet_name}")
                continue

            # 处理每个工作表
            df = excel_file.parse(sheet_name)
            records = dataframe_to_db_format(df)
            print(f"  找到 {len(records)} 条有效记录")

            # 批量插入/更新数据到devices_device表 - 存在则更新，不存在则插入
            if records:
                try:
                    # 使用表别名替代VALUES()函数
                    query = """
                        INSERT INTO `devices_device` 
                        (device_type_id, device_number, type, brand, model, status, details, image) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'images/default.jpg')
                        AS new_row
                        ON DUPLICATE KEY UPDATE
                        device_type_id = new_row.device_type_id,
                        type = new_row.type,
                        brand = new_row.brand,
                        model = new_row.model,
                        status = new_row.status,
                        details = new_row.details
                    """
                    data = [
                        (
                            sheet_id,
                            record['device_number'],
                            record['type'],
                            record['brand'],
                            record['model'],
                            record['status'],
                            record['details'],
                        )
                        for record in records
                    ]
                    cursor.executemany(query, data)
                    conn.commit()
                    print(f"  成功处理 {cursor.rowcount} 条记录")

                except mysql.connector.Error as e:
                    conn.rollback()
                    print(f"  处理设备数据时出错: {e}")

        print("所有记录处理成功！")

    except mysql.connector.Error as e:
        print(f"数据库操作错误: {e}")
        if conn and conn.is_connected():
            conn.rollback()

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("数据库连接已关闭。")
