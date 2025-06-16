#!/bin/bash

# 项目路径
PROJECT_DIR="/home/yourusername/device-manager-system"

# 进入项目目录
cd $PROJECT_DIR || exit

# 拉取最新代码
git pull origin main  # 替换main为项目分支名

# （可选）拉取后执行的操作（如安装依赖、重启服务）
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart gunicorn
sudo systemctl restart nginx