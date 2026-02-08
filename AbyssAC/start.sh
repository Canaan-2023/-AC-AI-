#!/bin/bash
# AbyssAC 启动脚本

echo "🧠 AbyssAC - 人工意识系统"
echo "=========================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.10+"
    exit 1
fi

# 检查依赖
if ! python3 -c "import gradio" 2>/dev/null; then
    echo "📦 正在安装依赖..."
    pip install -r requirements.txt
fi

# 启动系统
echo ""
echo "🚀 启动Gradio界面..."
echo "启动后请访问: http://localhost:7860"
echo ""

python3 main.py
