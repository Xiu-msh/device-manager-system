Run:
# 安装依赖库
# 导出依赖库，可以后续在其他平台可直接使用（pip list --format=freeze > requirements.txt）

pip install -r requirements.txt

# 生成models对应的迁移文件
python manage.py makemigrations

# 进行数据迁移
python manage.py migrate

# 执行数据库文件生产
运行create_sql_data.py文件

# 运行服务器
python manage.py runserver


TODO：
1、后台内容更新
    admin后台管理，数据统计还没有做

2、数据库批量导入文件(当前用的sqllite3())
    通过execl实现增加更新，
    SQLLite3目前还没有实现根据execl进行增删改

3、在设备详细界面增加返回到查询按钮
    在详细界面添加借用按钮
4、在设备详细界面增加设备异常提交按钮
    在详细界面添加借用按钮

5、当前为开发环境，生产环境未调试（用IIS发现调用不了static和media（可能开发环境下也有问题还未发现）,后台也进不去）


BUG:
1、如果筛选了字段后在查询 "已借用"点击后会没有模拟框弹出 -- 已修复 20250601
2、admin后台的图片上传保存路径错误 -- 已修复 20250601

