import cv2
import numpy as np
import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import io
import os
from typing import Optional, Tuple

class WatermarkProcessor:
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp']
    
    def convert_image_for_display(self, image):
        """
        将图像转换为适合在 Gradio 中显示的格式
        """
        if isinstance(image, Image.Image):
            print(f"转换图像：原始模式={image.mode}, 格式={getattr(image, 'format', 'Unknown')}")
            
            # 处理各种图像模式
            if image.mode == 'CMYK':
                # CMYK 转 RGB
                image = image.convert('RGB')
                print("CMYK -> RGB 转换完成")
            elif image.mode == 'L':
                # 灰度转 RGB
                image = image.convert('RGB')
                print("灰度 -> RGB 转换完成")
            elif image.mode == 'P':
                # 调色板模式转 RGB
                if 'transparency' in image.info:
                    image = image.convert('RGBA').convert('RGB')
                else:
                    image = image.convert('RGB')
                print("调色板 -> RGB 转换完成")
            elif image.mode == '1':
                # 1 位图像转 RGB
                image = image.convert('RGB')
                print("1 位图像 -> RGB 转换完成")
            elif image.mode == 'LA':
                # 灰度 + 透明度转 RGB
                image = image.convert('RGBA').convert('RGB')
                print("LA -> RGB 转换完成")
            elif image.mode not in ['RGB', 'RGBA']:
                # 其他模式统一转为 RGB
                image = image.convert('RGB')
                print(f"{image.mode} -> RGB 转换完成")
            
            print(f"最终模式：{image.mode}")
                
        return image
    
    def load_and_convert_image(self, image_path_or_pil):
        """
        加载并转换图像，确保兼容性
        """
        try:
            if isinstance(image_path_or_pil, str):
                # 从路径加载图像
                image = Image.open(image_path_or_pil)
            else:
                # 已经是 PIL 图像
                image = image_path_or_pil
            
            # 转换为显示格式
            converted_image = self.convert_image_for_display(image)
            
            print(f"图像信息：模式={image.mode}, 尺寸={image.size}, 格式={getattr(image, 'format', 'Unknown')}")
            print(f"转换后：模式={converted_image.mode}, 尺寸={converted_image.size}")
            
            return converted_image
            
        except Exception as e:
            print(f"图像加载/转换错误：{e}")
            raise e
    
    def add_text_watermark(self, 
                            image: np.ndarray, 
                            text: str, 
                            position: Tuple[int, int], 
                            font_size: int = 50, 
                            color: Tuple[int, int, int] = (255, 255, 255), 
                            opacity: float = 0.7, 
                            angle: float = 0,
                            repeat_mode: bool = False,
                            spacing_x: int = 200,
                            spacing_y: int = 100) -> np.ndarray:
        """
        添加文字水印
        """
        if not text.strip():
            return image
            
        # 转换为 PIL Image 进行文字处理
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # 创建透明图层
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 尝试使用系统字体，如果失败则使用默认字体
        try:
            # 在不同系统上尝试不同的字体路径，优先选择支持中文的字体
            font_paths = [
                # macOS 中文字体
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/Library/Fonts/Arial Unicode MS.ttf",
                # Linux 中文字体
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                # Windows 中文字体
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                # 英文字体备选
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "arial.ttf",  # Windows
                "C:/Windows/Fonts/arial.ttf"  # Windows 绝对路径
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        print(f"使用字体：{font_path}")
                        break
                    except Exception as e:
                        print(f"字体加载失败 {font_path}: {e}")
                        continue
            
            if font is None:
                font = ImageFont.load_default()
                print("使用默认字体")
        except Exception as e:
            font = ImageFont.load_default()
            print(f"字体加载异常：{e}, 使用默认字体")
        
        # 获取文字尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算透明度值 (确保有足够的可见度)
        alpha = max(50, int(255 * opacity))  # 最小透明度为 50，确保可见
        
        print(f"添加水印：文字='{text}', 颜色={color}, 透明度={alpha}, 重复模式={repeat_mode}")
        
        if repeat_mode:
            # 重复水印模式 - 在整个背景添加
            image_width, image_height = pil_image.size
            
            # 确保间距合理
            effective_spacing_x = max(spacing_x, text_width + 20)
            effective_spacing_y = max(spacing_y, text_height + 20)
            
            # 计算需要的行列数 (覆盖整个图像)
            cols = (image_width // effective_spacing_x) + 2
            rows = (image_height // effective_spacing_y) + 2
            
            print(f"重复水印：图像尺寸={image_width}x{image_height}, 行列数={rows}x{cols}, 间距={effective_spacing_x}x{effective_spacing_y}")
            
            watermark_count = 0
            for row in range(rows):
                for col in range(cols):
                    # 计算每个水印的位置
                    x = col * effective_spacing_x
                    y = row * effective_spacing_y
                    
                    # 错位排列，让水印更自然
                    if row % 2 == 1:
                        x += effective_spacing_x // 2
                    
                    # 确保水印在图像范围内或部分可见
                    if x < image_width + text_width and y < image_height + text_height and x > -text_width and y > -text_height:
                        if angle != 0:
                            # 为旋转文字创建临时图像
                            temp_size = max(text_width, text_height) + 100
                            temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
                            temp_draw = ImageDraw.Draw(temp_img)
                            temp_draw.text((temp_size//2 - text_width//2, temp_size//2 - text_height//2), 
                                         text, font=font, fill=(*color, alpha))
                            
                            # 旋转
                            rotated = temp_img.rotate(angle, expand=True)
                            
                            # 计算粘贴位置
                            paste_x = x - rotated.width // 2
                            paste_y = y - rotated.height // 2
                            
                            overlay.paste(rotated, (paste_x, paste_y), rotated)
                        else:
                            # 直接绘制文字
                            draw.text((x, y), text, font=font, fill=(*color, alpha))
                        
                        watermark_count += 1
            
            print(f"实际添加了 {watermark_count} 个水印")
        else:
            # 单个水印模式
            if angle != 0:
                # 创建临时图像用于旋转
                temp_size = max(text_width, text_height) + 100
                temp_img = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                temp_draw.text((50, 50), text, font=font, fill=(*color, alpha))
                
                # 旋转
                rotated = temp_img.rotate(angle, expand=True)
                
                # 计算粘贴位置
                paste_x = max(0, min(position[0], pil_image.width - rotated.width))
                paste_y = max(0, min(position[1], pil_image.height - rotated.height))
                
                overlay.paste(rotated, (paste_x, paste_y), rotated)
            else:
                # 直接绘制文字
                draw.text(position, text, font=font, fill=(*color, alpha))
        
        # 合并图层
        watermarked = Image.alpha_composite(pil_image.convert('RGBA'), overlay)
        
        # 转换回 OpenCV 格式
        result = cv2.cvtColor(np.array(watermarked.convert('RGB')), cv2.COLOR_RGB2BGR)
        return result
    
    def add_image_watermark(self, 
                           image: np.ndarray, 
                           watermark_image: np.ndarray, 
                           position: Tuple[int, int], 
                           scale: float = 0.2, 
                           opacity: float = 0.7, 
                           angle: float = 0) -> np.ndarray:
        """
        添加图片水印
        """
        h, w = image.shape[:2]
        
        # 调整水印大小
        wm_h, wm_w = watermark_image.shape[:2]
        new_width = int(w * scale)
        new_height = int(wm_h * new_width / wm_w)
        
        watermark_resized = cv2.resize(watermark_image, (new_width, new_height))
        
        # 如果需要旋转
        if angle != 0:
            center = (new_width // 2, new_height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            watermark_resized = cv2.warpAffine(watermark_resized, rotation_matrix, (new_width, new_height))
        
        # 确保位置在图像范围内
        y1 = max(0, min(position[1], h - new_height))
        y2 = y1 + new_height
        x1 = max(0, min(position[0], w - new_width))
        x2 = x1 + new_width
        
        # 调整水印区域大小以适应图像边界
        if y2 > h:
            y2 = h
            new_height = y2 - y1
            watermark_resized = watermark_resized[:new_height, :]
        
        if x2 > w:
            x2 = w
            new_width = x2 - x1
            watermark_resized = watermark_resized[:, :new_width]
        
        # 应用透明度
        roi = image[y1:y2, x1:x2]
        
        # 确保尺寸匹配
        if roi.shape[:2] != watermark_resized.shape[:2]:
            watermark_resized = cv2.resize(watermark_resized, (roi.shape[1], roi.shape[0]))
        
        # 混合图像
        result_roi = cv2.addWeighted(roi, 1 - opacity, watermark_resized, opacity, 0)
        
        # 创建结果图像
        result = image.copy()
        result[y1:y2, x1:x2] = result_roi
        
        return result

# 全局处理器实例
processor = WatermarkProcessor()

def process_watermark(image, watermark_type, text_content, text_font_size, text_color, 
                     watermark_image, position_x, position_y, opacity, angle, scale, 
                     repeat_mode, spacing_x, spacing_y):
    """
    处理水印添加的主函数
    """
    if image is None:
        return None, "请先上传图片"
    
    try:
        # 首先转换图像格式以确保兼容性
        converted_image = processor.load_and_convert_image(image)
        
        # 转换 PIL 图像为 OpenCV 格式
        if isinstance(converted_image, Image.Image):
            opencv_image = cv2.cvtColor(np.array(converted_image), cv2.COLOR_RGB2BGR)
        else:
            opencv_image = converted_image
        
        # 获取图像尺寸用于限制位置参数
        height, width = opencv_image.shape[:2]
        
        # 限制位置参数在合理范围内
        position_x = max(0, min(int(position_x), width - 1))
        position_y = max(0, min(int(position_y), height - 1))
        position = (position_x, position_y)
        
        # 限制字体大小在合理范围内
        text_font_size = max(1, min(int(text_font_size), 500))
        
        # 限制透明度在有效范围内
        opacity = max(0.0, min(float(opacity), 1.0))
        
        # 限制角度在有效范围内
        angle = max(-180, min(float(angle), 180))
        
        # 限制缩放比例在有效范围内
        scale = max(0.01, min(float(scale), 2.0))
        
        # 限制间距参数
        spacing_x = max(50, min(int(spacing_x), 500))
        spacing_y = max(50, min(int(spacing_y), 300))
        
        if watermark_type == "文字水印":
            if not text_content.strip():
                return converted_image, "请输入水印文字"
            
            # 转换颜色格式 - 增强错误处理
            try:
                print(f"原始颜色值：{text_color}")
                
                if isinstance(text_color, str) and text_color.startswith('#'):
                    # 处理 #FFFFFF 格式
                    hex_color = text_color.lstrip('#')
                    if len(hex_color) == 6:
                        color_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    elif len(hex_color) == 3:
                        # 处理 #FFF 格式
                        color_rgb = tuple(int(hex_color[i]*2, 16) for i in range(3))
                    else:
                        raise ValueError("Invalid hex color format")
                elif isinstance(text_color, str) and text_color.startswith('rgb'):
                    # 处理 rgb(255,255,255) 格式
                    import re
                    rgb_values = re.findall(r'\d+', text_color)
                    if len(rgb_values) >= 3:
                        color_rgb = tuple(int(rgb_values[i]) for i in range(3))
                    else:
                        raise ValueError("Invalid rgb color format")
                elif isinstance(text_color, (list, tuple)) and len(text_color) >= 3:
                    # 处理已经是 RGB 元组的情况
                    color_rgb = tuple(int(c) for c in text_color[:3])
                else:
                    # 尝试直接解析为 hex（去掉#）
                    if isinstance(text_color, str):
                        clean_color = text_color.lstrip('#')
                        if len(clean_color) == 6:
                            color_rgb = tuple(int(clean_color[i:i+2], 16) for i in (0, 2, 4))
                        else:
                            raise ValueError("Unknown color format")
                    else:
                        raise ValueError("Unknown color format")
                
                # 确保颜色值在有效范围内
                color_rgb = tuple(max(0, min(255, int(c))) for c in color_rgb)
                print(f"解析后颜色值：{color_rgb}")
                
            except (ValueError, IndexError, TypeError) as e:
                print(f"颜色解析错误：{e}, 原始值：{text_color}, 使用默认灰色")
                color_rgb = (128, 128, 128)  # 使用灰色作为默认
            
            result = processor.add_text_watermark(
                opencv_image, text_content, position, 
                text_font_size, color_rgb, opacity, angle,
                repeat_mode, spacing_x, spacing_y
            )
        
        elif watermark_type == "图片水印":
            if watermark_image is None:
                return converted_image, "请上传水印图片"
            
            # 转换水印图片格式并转为 OpenCV 格式
            converted_watermark = processor.load_and_convert_image(watermark_image)
            if isinstance(converted_watermark, Image.Image):
                watermark_cv = cv2.cvtColor(np.array(converted_watermark), cv2.COLOR_RGB2BGR)
            else:
                watermark_cv = converted_watermark
            
            result = processor.add_image_watermark(
                opencv_image, watermark_cv, position, 
                scale, opacity, angle
            )
        
        else:
            return converted_image, "请选择水印类型"
        
        # 转换回 PIL 格式用于显示
        result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        return result_pil, "水印添加成功！"
        
    except Exception as e:
        # 如果处理失败，返回转换后的原图
        try:
            converted_image = processor.load_and_convert_image(image)
            return converted_image, f"处理失败：{str(e)}"
        except:
            return image, f"处理失败：{str(e)}"

def create_gradio_interface():
    """
    创建 Gradio 界面
    """
    # 自定义CSS样式
    custom_css = """
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    .section-header {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
        text-align: center;
    }
    .tips-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #ff6b6b;
        margin: 1rem 0;
    }
    .tips-box h3 {
        color: #2d3436 !important;
        font-weight: 600;
        margin-top: 0;
    }
    .tips-box h4 {
        color: #2d3436 !important;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .tips-box li {
        color: #2d3436 !important;
        font-weight: 400;
        line-height: 1.6;
        margin-bottom: 0.3rem;
    }
    .control-group {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .quick-buttons {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0;
    }
    /* 调整图片上传区域的高度和对齐 */
    .image-upload-container {
        min-height: 350px;
    }
    .image-preview-container {
        min-height: 450px;
    }
    """
    
    with gr.Blocks(
        title="图片水印工具", 
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="pink",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter")
        ),
        css=custom_css
    ) as demo:
        
        # 主标题区域
        with gr.Row():
            with gr.Column():
                gr.HTML("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">
                        🎨 图片水印添加工具
                    </h1>
                    <p style="margin: 1rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                        专业的图片水印处理工具，支持文字和图片水印，多种样式自定义
                    </p>
                </div>
                """)
        
        # 使用说明区域
        with gr.Row():
            with gr.Column():
                gr.HTML("""
                <div class="tips-box">
                    <h3>📋 使用指南</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                        <div>
                            <h4>🚀 快速开始</h4>
                            <ul style="margin: 0; padding-left: 1.2rem;">
                                <li>上传您的图片文件</li>
                                <li>选择水印类型（文字/图片）</li>
                                <li>调整水印参数</li>
                                <li>点击"添加水印"按钮</li>
                            </ul>
                        </div>
                        <div>
                            <h4>💡 专业建议</h4>
                            <ul style="margin: 0; padding-left: 1.2rem;">
                                <li>透明度建议设置在 0.3-0.7</li>
                                <li>使用重复模式可防止裁剪</li>
                                <li>适当的倾斜角度更美观</li>
                                <li>支持 JPG、PNG、TIFF 等格式</li>
                            </ul>
                        </div>
                    </div>
                </div>
                """)
        
        # 主要工作区域
        with gr.Row(equal_height=True):
            # 左侧控制面板
            with gr.Column(scale=2):
                gr.HTML('<div class="section-header"><h3 style="margin: 0;">⚙️ 控制面板</h3></div>')
                
                with gr.Group():
                    gr.Markdown("### 📁 图片上传")
                    input_image = gr.Image(
                        label="选择图片文件", 
                        type="pil",
                        sources=["upload", "clipboard"],
                        height=350,  # 增加高度
                        elem_classes=["image-upload-container"]
                    )
                    
                    # TIFF 专用上传（紧凑布局）
                    with gr.Row():
                        with gr.Column(scale=3):
                            tiff_file = gr.File(
                                label="TIFF 专用上传",
                                file_types=[".tif", ".tiff"],
                                visible=False,
                                scale=2
                            )
                        with gr.Column(scale=1):
                            show_tiff_uploader = gr.Button(
                                "🖼️ TIFF", 
                                variant="secondary", 
                                size="sm"
                            )
                    
                    gr.Markdown("""
                    **支持格式:** JPG, PNG, TIFF, BMP, WebP  
                    **提示:** TIFF 文件会自动转换为 Web 兼容格式
                    """, elem_classes=["tips-text"])
                
                # 水印类型选择
                with gr.Group():
                    gr.Markdown("### 🎯 水印类型")
                    watermark_type = gr.Radio(
                        choices=["文字水印", "图片水印"], 
                        value="文字水印", 
                        label="选择类型",
                        interactive=True
                    )
                
                # 文字水印设置
                with gr.Group(visible=True) as text_group:
                    gr.Markdown("### ✏️ 文字水印配置")
                    
                    text_content = gr.Textbox(
                        label="水印文字", 
                        placeholder="输入您的水印文字...",
                        value="WATERMARK",
                        lines=2
                    )
                    
                    # 快速文字选择
                    gr.Markdown("**快速选择:**")
                    with gr.Row():
                        gr.Button("© 版权保护", size="sm").click(
                            lambda: "© 版权保护", outputs=[text_content]
                        )
                        gr.Button("🚫 禁止盗用", size="sm").click(
                            lambda: "🚫 禁止盗用", outputs=[text_content]
                        )
                        gr.Button("WATERMARK", size="sm").click(
                            lambda: "WATERMARK", outputs=[text_content]
                        )
                        gr.Button("SAMPLE", size="sm").click(
                            lambda: "SAMPLE", outputs=[text_content]
                        )
                    
                    with gr.Row():
                        text_font_size = gr.Slider(
                            minimum=10, maximum=200, value=40, 
                            label="字体大小", step=5
                        )
                        text_color = gr.ColorPicker(
                            label="文字颜色", 
                            value="#FF4757"
                        )
                    
                    # 颜色快选
                    gr.Markdown("**常用颜色:**")
                    with gr.Row():
                        gr.Button("🔴", size="sm").click(lambda: "#FF4757", outputs=[text_color])
                        gr.Button("⚫", size="sm").click(lambda: "#2F3542", outputs=[text_color])
                        gr.Button("🔵", size="sm").click(lambda: "#3742FA", outputs=[text_color])
                        gr.Button("⚪", size="sm").click(lambda: "#F1F2F6", outputs=[text_color])
                        gr.Button("🟡", size="sm").click(lambda: "#FFA502", outputs=[text_color])
                        gr.Button("🟢", size="sm").click(lambda: "#2ED573", outputs=[text_color])
                    
                    # 重复模式设置
                    repeat_mode = gr.Checkbox(
                        label="🔄 重复水印模式（全图覆盖）",
                        value=True,
                        info="开启后水印将铺满整个图片"
                    )
                    
                    with gr.Row():
                        spacing_x = gr.Slider(
                            minimum=50, maximum=400, value=150,
                            label="水平间距", step=10
                        )
                        spacing_y = gr.Slider(
                            minimum=50, maximum=300, value=100,
                            label="垂直间距", step=10
                        )
                
                # 图片水印设置
                with gr.Group(visible=False) as image_group:
                    gr.Markdown("### 🖼️ 图片水印配置")
                    watermark_image = gr.Image(
                        label="水印图片", 
                        type="pil",
                        sources=["upload"],
                        height=200
                    )
                    scale = gr.Slider(
                        minimum=0.05, maximum=1.0, value=0.2, 
                        label="水印大小比例", step=0.05
                    )
                
                # 通用参数设置
                with gr.Group():
                    gr.Markdown("### 🎛️ 高级设置")
                    
                    with gr.Row():
                        position_x = gr.Slider(
                            minimum=0, maximum=2000, value=100, 
                            label="水平位置 (px)", step=10
                        )
                        position_y = gr.Slider(
                            minimum=0, maximum=2000, value=100, 
                            label="垂直位置 (px)", step=10
                        )
                    
                    with gr.Row():
                        opacity = gr.Slider(
                            minimum=0.1, maximum=1.0, value=0.4, step=0.05,
                            label="透明度", 
                            info="值越小越透明"
                        )
                        angle = gr.Slider(
                            minimum=-180, maximum=180, value=-30, step=5,
                            label="旋转角度 (°)",
                            info="负值为逆时针"
                        )
                
                # 处理按钮
                with gr.Row():
                    process_btn = gr.Button(
                        "🎯 添加水印", 
                        variant="primary", 
                        size="lg",
                        scale=2
                    )
                    gr.Button(
                        "🔄 重置参数", 
                        variant="secondary",
                        size="lg",
                        scale=1
                    ).click(
                        lambda: [
                            "WATERMARK", 40, "#FF4757", True, 150, 100,
                            100, 100, 0.4, -30, 0.2
                        ],
                        outputs=[
                            text_content, text_font_size, text_color, repeat_mode,
                            spacing_x, spacing_y, position_x, position_y,
                            opacity, angle, scale
                        ]
                    )
            
            # 右侧结果展示
            with gr.Column(scale=2):
                gr.HTML('<div class="section-header"><h3 style="margin: 0;">📤 处理结果</h3></div>')
                
                with gr.Group():
                    gr.Markdown("### 📤 水印效果预览")
                    output_image = gr.Image(
                        label="水印效果预览", 
                        type="pil",
                        height=350,  # 与左侧上传区域高度一致
                        interactive=False,  # 禁止交互，只用于显示
                        show_download_button=False,  # 移除下载按钮，使用下方的专用按钮
                        elem_classes=["image-preview-container"]
                    )
                    
                    status_text = gr.Textbox(
                        label="处理状态", 
                        interactive=False,
                        max_lines=3
                    )
                    
                    # 下载和分享按钮
                    with gr.Row():
                        download_btn = gr.DownloadButton(
                            "💾 下载图片", 
                            variant="primary",
                            size="lg",
                            scale=2
                        )
                        # gr.Button(
                        #     "📋 复制链接", 
                        #     variant="secondary",
                        #     size="lg",
                        #     scale=1
                        # )
                
                # 处理信息面板
                with gr.Group():
                    gr.Markdown("### 📊 处理信息")
                    info_display = gr.JSON(
                        label="图片信息",
                        visible=False
                    )
        
        # 事件处理函数保持不变
        def toggle_tiff_uploader():
            return gr.update(visible=True)
        
        def process_tiff_file(file):
            if file is None:
                return None
            
            try:
                image = Image.open(file.name)
                converted_image = processor.load_and_convert_image(image)
                return converted_image
            except Exception as e:
                print(f"TIFF 文件处理错误：{e}")
                return None
        
        def toggle_watermark_settings(watermark_type):
            if watermark_type == "文字水印":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)
        
        def update_download(result_image):
            if result_image is not None:
                temp_path = "watermarked_image.png"
                result_image.save(temp_path)
                return gr.update(value=temp_path, visible=True)
            return gr.update(visible=False)
        
        def handle_image_upload(image):
            if image is None:
                return None, gr.update(visible=False)
            
            try:
                if hasattr(image, 'format') and image.format in ['TIFF', 'TIF']:
                    print(f"检测到 TIFF 格式图像，正在转换...")
                    converted_image = processor.load_and_convert_image(image)
                    info = {
                        "格式": "TIFF (已转换)",
                        "尺寸": f"{image.size[0]} x {image.size[1]}",
                        "模式": image.mode
                    }
                    return converted_image, gr.update(value=info, visible=True)
                elif hasattr(image, 'mode') and image.mode in ['CMYK', 'L', 'P', '1']:
                    converted_image = processor.load_and_convert_image(image)
                    info = {
                        "格式": getattr(image, 'format', 'Unknown'),
                        "尺寸": f"{image.size[0]} x {image.size[1]}",
                        "模式": f"{image.mode} (已转换为RGB)"
                    }
                    return converted_image, gr.update(value=info, visible=True)
                else:
                    info = {
                        "格式": getattr(image, 'format', 'Unknown'),
                        "尺寸": f"{image.size[0]} x {image.size[1]}",
                        "模式": image.mode
                    }
                    return image, gr.update(value=info, visible=True)
                    
            except Exception as e:
                print(f"图像上传处理错误：{e}")
                try:
                    if hasattr(image, 'convert'):
                        return image.convert('RGB'), gr.update(visible=False)
                except:
                    pass
                return image, gr.update(visible=False)
        
        # 绑定事件
        show_tiff_uploader.click(
            fn=toggle_tiff_uploader,
            outputs=[tiff_file]
        )
        
        tiff_file.change(
            fn=process_tiff_file,
            inputs=[tiff_file],
            outputs=[input_image]
        )
        
        watermark_type.change(
            fn=toggle_watermark_settings,
            inputs=[watermark_type],
            outputs=[text_group, image_group]
        )
        
        input_image.upload(
            fn=handle_image_upload,
            inputs=[input_image],
            outputs=[input_image, info_display]
        )
        
        process_btn.click(
            fn=process_watermark,
            inputs=[
                input_image, watermark_type, text_content, text_font_size, text_color,
                watermark_image, position_x, position_y, opacity, angle, scale,
                repeat_mode, spacing_x, spacing_y
            ],
            outputs=[output_image, status_text]
        ).then(
            fn=update_download,
            inputs=[output_image],
            outputs=[download_btn]
        )

    return demo

if __name__ == "__main__":
    # 创建并启动应用
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    ) 