#!/bin/bash

# 启动域名监控服务
# 使用方法: ./start-monitor.sh

cd "$(dirname "$0")"

echo "=========================================="
echo "  启动域名监控服务"
echo "=========================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python"
    exit 1
fi

# 检查 requests 模块
python3 -c "import requests" 2>/dev/null || python -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "警告: requests 模块未安装"
    echo "正在安装..."
    pip install requests || pip3 install requests
fi

# 启动监控
python3 ipScan.py --monitor 2>/dev/null || python ipScan.py --monitor
