#!/bin/bash

PROJECT_DIR="/home/shin/device-manager-system"
LOG_FILE="/home/shin/tasks/pull_device-manager-system_log.txt"

echo "=== $(date) ===" >> "$LOG_FILE"

# 拉取代码前记录当前提交ID
cd "$PROJECT_DIR" || { echo "错误：无法进入项目目录！" >> "$LOG_FILE"; exit 1; }
OLD_COMMIT=$(git rev-parse HEAD)

# 拉取最新代码
git pull origin main >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "错误：拉取代码失败！" >> "$LOG_FILE"
    exit 1
fi

# 拉取后记录新提交ID
NEW_COMMIT=$(git rev-parse HEAD)

# 检查是否有新提交
if [ "$OLD_COMMIT" = "$NEW_COMMIT" ]; then
    echo "没有新代码更新，跳过后续部署步骤" >> "$LOG_FILE"
    exit 0
fi

echo "检测到代码更新，开始部署..." >> "$LOG_FILE"

# 激活虚拟环境并安装依赖（使用www-data权限）
echo "正在更新依赖..." >> "$LOG_FILE"
sudo -u www-data "$PROJECT_DIR/venv/bin/pip" install -r requirements.txt >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "错误：安装依赖失败！" >> "$LOG_FILE"
    exit 1
fi

# 收集静态文件（使用www-data权限）
echo "正在收集静态文件..." >> "$LOG_FILE"
sudo -u www-data "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/manage.py" collectstatic --noinput >> "$LOG_FILE" 2>&1

# 重启gunicorn服务
echo "正在重启gunicorn服务..." >> "$LOG_FILE"
sudo systemctl restart gunicorn >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "错误：重启gunicorn失败！" >> "$LOG_FILE"
    exit 1
fi

# 重启Nginx服务（修复了原脚本中的语法错误）
echo "正在重启Nginx服务..." >> "$LOG_FILE"
sudo systemctl restart nginx >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "错误：重启Nginx失败！" >> "$LOG_FILE"
    exit 1
fi

echo "部署成功！" >> "$LOG_FILE"
exit 0