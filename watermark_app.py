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
        # 转换 PIL 图像为 OpenCV 格式
        if isinstance(image, Image.Image):
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            opencv_image = image
        
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
                return image, "请输入水印文字"
            
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
                return image, "请上传水印图片"
            
            # 转换水印图片为 OpenCV 格式
            if isinstance(watermark_image, Image.Image):
                watermark_cv = cv2.cvtColor(np.array(watermark_image), cv2.COLOR_RGB2BGR)
            else:
                watermark_cv = watermark_image
            
            result = processor.add_image_watermark(
                opencv_image, watermark_cv, position, 
                scale, opacity, angle
            )
        
        else:
            return image, "请选择水印类型"
        
        # 转换回 PIL 格式用于显示
        result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
        return result_pil, "水印添加成功！"
        
    except Exception as e:
        return image, f"处理失败：{str(e)}"

def create_gradio_interface():
    """
    创建 Gradio 界面
    """
    with gr.Blocks(title="图片水印工具", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🎨 图片水印添加工具")
        gr.Markdown("支持为图片添加文字或图片水印，支持多种参数调整")
        
        with gr.Row():
            with gr.Column(scale=1):
                # 输入区域
                gr.Markdown("## 📁 输入设置")
                input_image = gr.Image(
                    label="上传图片", 
                    type="pil",
                    sources=["upload", "clipboard"]
                )
                
                watermark_type = gr.Radio(
                    choices=["文字水印", "图片水印"], 
                    value="文字水印", 
                    label="水印类型"
                )
                
                # 文字水印设置
                with gr.Group(visible=True) as text_group:
                    gr.Markdown("### ✏️ 文字水印设置")
                    text_content = gr.Textbox(
                        label="水印文字", 
                        placeholder="请输入水印文字",
                        value="测试水印"
                    )
                    
                    # 添加快速选择按钮
                    with gr.Row():
                        gr.Button("防盗用标记", size="sm").click(
                            lambda: "防盗用标记", 
                            outputs=[text_content]
                        )
                        gr.Button("WATERMARK", size="sm").click(
                            lambda: "WATERMARK", 
                            outputs=[text_content]
                        )
                        gr.Button("版权所有", size="sm").click(
                            lambda: "版权所有", 
                            outputs=[text_content]
                        )
                    text_font_size = gr.Slider(
                        minimum=10, maximum=200, value=30, 
                        label="字体大小"
                    )
                    text_color = gr.ColorPicker(
                        label="文字颜色", 
                        value="#FF0000"  # 改为红色，更容易看见
                    )
                    
                    # 添加快速颜色选择
                    with gr.Row():
                        gr.Button("🔴 红色", size="sm").click(
                            lambda: "#FF0000", 
                            outputs=[text_color]
                        )
                        gr.Button("⚫ 黑色", size="sm").click(
                            lambda: "#000000", 
                            outputs=[text_color]
                        )
                        gr.Button("🔵 蓝色", size="sm").click(
                            lambda: "#0000FF", 
                            outputs=[text_color]
                        )
                        gr.Button("⚪ 白色", size="sm").click(
                            lambda: "#FFFFFF", 
                            outputs=[text_color]
                        )
                    
                    # 重复水印设置
                    repeat_mode = gr.Checkbox(
                        label="🔄 重复水印模式 (背景铺满)",
                        value=True  # 默认开启重复模式
                    )
                    
                    with gr.Row():
                        spacing_x = gr.Slider(
                            minimum=50, maximum=500, value=150,  # 减小间距
                            label="水平间距"
                        )
                        spacing_y = gr.Slider(
                            minimum=50, maximum=300, value=80,   # 减小间距
                            label="垂直间距"
                        )
                
                # 图片水印设置
                with gr.Group(visible=False) as image_group:
                    gr.Markdown("### 🖼️ 图片水印设置")
                    watermark_image = gr.Image(
                        label="水印图片", 
                        type="pil",
                        sources=["upload"]
                    )
                    scale = gr.Slider(
                        minimum=0.05, maximum=1.0, value=0.2, 
                        label="水印大小比例"
                    )
                
                # 通用设置
                gr.Markdown("### ⚙️ 通用设置")
                with gr.Row():
                    position_x = gr.Slider(
                        minimum=0, maximum=2000, value=50, 
                        label="水印 X 位置"
                    )
                    position_y = gr.Slider(
                        minimum=0, maximum=2000, value=50, 
                        label="水印 Y 位置"
                    )
                
                with gr.Row():
                    opacity = gr.Slider(
                        minimum=0.1, maximum=1.0, value=0.3, step=0.1,  # 降低默认透明度
                        label="透明度"
                    )
                    angle = gr.Slider(
                        minimum=-180, maximum=180, value=-30,  # 默认倾斜角度
                        label="倾斜角度 (度)"
                    )
                
                # 处理按钮
                process_btn = gr.Button("🎯 添加水印", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                # 输出区域
                gr.Markdown("## 📤 输出结果")
                output_image = gr.Image(label="处理结果", type="pil")
                status_text = gr.Textbox(label="状态信息", interactive=False)
                
                # 下载按钮
                download_btn = gr.DownloadButton(
                    "💾 下载图片", 
                    variant="secondary"
                )
        
        # 事件处理
        def toggle_watermark_settings(watermark_type):
            if watermark_type == "文字水印":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)
        
        watermark_type.change(
            fn=toggle_watermark_settings,
            inputs=[watermark_type],
            outputs=[text_group, image_group]
        )
        
        def update_download(result_image):
            if result_image is not None:
                # 保存临时文件
                temp_path = "watermarked_image.png"
                result_image.save(temp_path)
                return gr.update(value=temp_path, visible=True)
            return gr.update(visible=False)
        
        # 处理按钮点击事件
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
        
        # 示例
        gr.Markdown("""
        ## �� 使用说明
        1. **上传图片**: 支持 JPG、PNG、TIFF 等常见格式
        2. **选择水印类型**: 文字水印或图片水印
        3. **调整参数**: 
           - 位置：调整水印在图片中的位置
           - 透明度：控制水印的透明程度
           - 角度：设置水印的倾斜角度
           - 大小：(图片水印) 控制水印相对于原图的大小比例
        4. **点击处理**: 生成带水印的图片
        5. **下载结果**: 保存处理后的图片
        
        ## 💡 小贴士
        - 建议水印透明度设置在 0.3-0.8 之间效果最佳
        - 文字水印支持调整颜色和字体大小
        - 图片水印会自动根据比例缩放
        """)
    
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