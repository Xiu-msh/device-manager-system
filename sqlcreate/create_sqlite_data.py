import pandas as pd
import sqlite3
import json
from datetime import datetime


# 将 DataFrame 转换为适合插入数据库的格式
def dataframe_to_db_format(df):
    records = []
    # 确定需要处理的列（排除特定列）
    exclude_columns = ['设备编号', '设备类型', '品牌', '型号', '状态']
    select_columns = [col for col in df.columns if col not in exclude_columns]

    for _, row in df.iterrows():
        if pd.notna(row['设备编号']):
            # 提取基本字段
            device_number = row['设备编号']
            type_ = row['设备类型']
            brand = row['品牌']
            model = row['型号']
            status = row['状态']

            # 提取详细信息列
            details_values = row[select_columns]  # 获取不在排除列表中的列
            details = dict(zip(select_columns, details_values))

            # 处理缺失值和 Timestamp 对象
            for key, value in details.items():
                if pd.isna(value):
                    details[key] = None
                elif isinstance(value, pd.Timestamp):
                    # 将 Timestamp 对象转换为字符串
                    details[key] = value.strftime('%Y-%m-%d %H:%M:%S')

            # 构造记录
            record = {
                'device_number': device_number,
                'type': type_,
                'brand': brand,
                'model': model,
                'status': status,
                'details': json.dumps(details, ensure_ascii=False),  # 转换为 JSON 字符串
            }
            records.append(record)
    return records


if __name__ == '__main__':
    # 读取 Excel 文件
    excel_file = pd.ExcelFile('device.xlsx')

    # 创建SQLite数据库连接
    conn = sqlite3.connect(r'/device_manager/db.sqlite3')
    cursor = conn.cursor()

    try:
        # 开始事务
        conn.execute("BEGIN TRANSACTION")

        # 预处理：获取所有已存在的设备类型，避免重复查询
        cursor.execute("SELECT name, id FROM devices_devicetype")
        existing_types = {name: id for name, id in cursor.fetchall()}

        for sheet_name in excel_file.sheet_names:
            # 插入或忽略Sheet名称到表devicetype
            if sheet_name not in existing_types:
                cursor.execute('INSERT OR IGNORE INTO devices_devicetype (name) VALUES (?)', (sheet_name,))
                # 获取新插入的ID
                if cursor.rowcount > 0:
                    cursor.execute('SELECT last_insert_rowid()')
                    sheet_id = cursor.fetchone()[0]
                    existing_types[sheet_name] = sheet_id
                else:
                    # 如果已经存在，获取ID
                    cursor.execute('SELECT id FROM devices_devicetype WHERE name = ?', (sheet_name,))
                    existing_types[sheet_name] = cursor.fetchone()[0]
            else:
                sheet_id = existing_types[sheet_name]

            # 针对每一个sheet单独操作
            df = excel_file.parse(sheet_name)
            records = dataframe_to_db_format(df)

            # 准备批量插入/更新数据
            for record in records:
                # 使用UPSERT (INSERT OR REPLACE) 语法
                # 当前存在问题(还是会更新过ID)
                cursor.execute("""
                    INSERT INTO devices_device 
                    (device_type_id, device_number, type, brand, model, status, details, image) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'images/default.jpg')
                    ON CONFLICT(device_type_id, device_number) DO UPDATE SET
                        type = excluded.type,
                        brand = excluded.brand,
                        model = excluded.model,
                        status = excluded.status,
                        details = excluded.details,
                        image = excluded.image
                """, (
                    sheet_id,
                    record['device_number'],
                    record['type'],
                    record['brand'],
                    record['model'],
                    record['status'],
                    record['details'],
                ))

            print(f"Sheet '{sheet_name}' 处理完成，共 {len(records)} 条记录")

        # 提交事务
        conn.commit()
        print("所有记录处理成功！")

    except sqlite3.Error as e:
        # 发生错误时回滚
        conn.rollback()
        print(f"数据库操作错误: {e}")
    except Exception as e:
        conn.rollback()
        print(f"发生错误: {e}")
    finally:
        # 确保无论是否发生错误都关闭连接
        conn.close()
        print("数据库连接已关闭。")