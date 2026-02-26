#!/bin/bash

# Change to project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Get the computer's IP address
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

echo "=========================================="
echo "期权策略分析平台启动中..."
echo "=========================================="
echo ""
echo "本地访问地址: http://localhost:8501"
echo "局域网访问地址: http://$IP_ADDRESS:8501"
echo ""
echo "手机访问步骤:"
echo "1. 确保手机和电脑连接同一WiFi"
echo "2. 在手机浏览器输入: http://$IP_ADDRESS:8501"
echo ""
echo "=========================================="
echo ""

# Run Streamlit app
streamlit run app.py
