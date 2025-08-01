#!/bin/bash

echo "🎨 图片水印添加工具启动中..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "watermark_env" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv watermark_env
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source watermark_env/bin/activate

# 检查依赖是否安装
echo "📦 检查依赖..."
if ! python -c "import cv2, gradio, PIL, numpy" 2>/dev/null; then
    echo "📥 安装依赖包..."
    pip3 install -r requirements.txt
fi

echo "🚀 启动应用..."
echo "💡 应用启动后请在浏览器中访问: http://localhost:7860"
echo "⏹️ 按 Ctrl+C 停止应用"
echo ""

python3 watermark_app.py 