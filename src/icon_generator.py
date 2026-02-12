"""
动态图标生成模块
"""
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple
import io


class IconGenerator:
    """托盘图标生成器"""

    # 颜色定义
    COLORS = {
        'green': (76, 175, 80),      # 正常 - 绿色
        'yellow': (255, 193, 7),     # 警告 - 黄色
        'red': (244, 67, 54),        # 危险 - 红色
        'gray': (158, 158, 158),     # 未知 - 灰色
    }

    def __init__(self, size: int = 64):
        """
        初始化图标生成器

        Args:
            size: 图标尺寸 (像素)
        """
        self.size = size

    def create_icon(self, percentage: float, show_text: bool = True) -> Image.Image:
        """
        创建状态图标

        Args:
            percentage: 使用百分比 (0-100)
            show_text: 是否在图标上显示百分比文字

        Returns:
            PIL Image 对象
        """
        # 选择颜色
        if percentage >= 90:
            color = self.COLORS['red']
        elif percentage >= 70:
            color = self.COLORS['yellow']
        else:
            color = self.COLORS['green']

        # 创建透明背景图像
        image = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制圆形背景
        margin = 2
        draw.ellipse(
            [margin, margin, self.size - margin, self.size - margin],
            fill=color,
            outline=(255, 255, 255, 200),
            width=2
        )

        # 绘制百分比文字
        if show_text and self.size >= 32:
            text = f"{int(percentage)}"
            self._draw_centered_text(draw, text, (255, 255, 255))

        return image

    def create_pie_icon(self, percentage: float) -> Image.Image:
        """
        创建饼图样式的图标

        Args:
            percentage: 使用百分比 (0-100)

        Returns:
            PIL Image 对象
        """
        # 选择颜色
        if percentage >= 90:
            fill_color = self.COLORS['red']
        elif percentage >= 70:
            fill_color = self.COLORS['yellow']
        else:
            fill_color = self.COLORS['green']

        bg_color = (200, 200, 200, 255)

        # 创建透明背景图像
        image = Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        margin = 2
        box = [margin, margin, self.size - margin, self.size - margin]

        # 绘制背景圆
        draw.ellipse(box, fill=bg_color)

        # 绘制使用量扇形 (从顶部开始，顺时针)
        if percentage > 0:
            start_angle = -90  # 从顶部开始
            end_angle = start_angle + (percentage / 100) * 360
            draw.pieslice(box, start_angle, end_angle, fill=fill_color)

        # 绘制边框
        draw.ellipse(box, outline=(100, 100, 100, 255), width=2)

        return image

    def _draw_centered_text(self, draw: ImageDraw.Draw, text: str, color: Tuple[int, int, int]):
        """在图标中央绘制文字"""
        try:
            # 尝试使用 Arial 字体
            font_size = self.size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # 使用默认字体
            font = ImageFont.load_default()

        # 获取文字边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算居中位置
        x = (self.size - text_width) // 2
        y = (self.size - text_height) // 2 - 2

        # 绘制文字
        draw.text((x, y), text, fill=color, font=font)

    def get_color_for_percentage(self, percentage: float) -> str:
        """根据百分比返回颜色名称"""
        if percentage >= 90:
            return 'red'
        elif percentage >= 70:
            return 'yellow'
        else:
            return 'green'


# 全局图标生成器实例
icon_generator = IconGenerator(size=64)
