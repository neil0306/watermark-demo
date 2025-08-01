@echo off
chcp 65001 >nul
echo 🎨 图片水印添加工具启动中...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "watermark_env" (
    echo 📦 创建虚拟环境...
    python -m venv watermark_env
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call watermark_env\Scripts\activate.bat

REM 检查依赖是否安装
echo 📦 检查依赖...
python -c "import cv2, gradio, PIL, numpy" 2>nul
if errorlevel 1 (
    echo 📥 安装依赖包...
    pip install -r requirements.txt
)

echo 🚀 启动应用...
echo 💡 应用启动后请在浏览器中访问: http://localhost:7860
echo ⏹️ 按 Ctrl+C 停止应用
echo.

python watermark_app.py
pause