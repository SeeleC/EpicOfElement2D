# -*- coding: utf-8 -*-
"""UI 绘制工具：与 Batch 协作的形状与文字基元。

坐标约定（全项目统一）：**屏幕左上角为原点，X 向右、Y 向下为正**（见 config 注释）。
而 arcade 的 shapes / Text 默认采用「左下角为原点、Y 向上」的 OpenGL 坐标。
因此本模块在把每个基元的坐标传给 arcade 前做一次垂直翻转（水平方向不变）：
    GL_y = VIEWPORT_H - y            （circle / 文本锚点）
    GL_y = VIEWPORT_H - y - h/2      （矩形 / 边框矩形，y 为其顶边，arcade 以中心定位）

调用方无需关心此差异，只需按「左上原点、Y 向下」传参即可。
窗口高度由 Game 在每帧 render 前通过 set_viewport_h() 提供。

arcade 3.x：ShapeElementList / create_* 系列已移动到 arcade.shape_list 子模块。
"""
from arcade import shape_list, Text
from .. import config

# 当前视口高度（由调用方每帧 render 前设置）。把「左上、Y 向下」坐标
# 翻转成 arcade 的「左下、Y 向上」坐标。
VIEWPORT_H = 0


class Batch:
    """arcade 版批处理：一个 ShapeElementList（批量形状）+ 若干 Text（文字）。"""
    def __init__(self):
        self.shapes = shape_list.ShapeElementList()
        self.texts = []

    def add_shape(self, shape):
        self.shapes.append(shape)
        return shape

    def add_text(self, text):
        self.texts.append(text)
        return text

    def draw(self):
        self.shapes.draw()
        for t in self.texts:
            t.draw()


def set_viewport_h(h):
    global VIEWPORT_H
    VIEWPORT_H = h


def begin_frame():
    """为兼容旧调用保留；Batch 每帧重建已天然防累积，无需额外清理。"""
    pass


def _gl_y_top(y, h=0):
    """矩形顶边 y（左上原点 Y 向下）-> arcade 的矩形中心 y（左下原点 Y 向上）。"""
    return VIEWPORT_H - y - h / 2


def add_rect(batch, x, y, w, h, color, group=None):
    """向 batch 添加一个矩形。y 为其顶边（左上原点 Y 向下）。"""
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    s = shape_list.create_rectangle_filled(x + w / 2, _gl_y_top(y, h), w, h, (r, g, b, a))
    return batch.add_shape(s)


def add_circle(batch, x, y, radius, color, group=None, segments=24):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    c = shape_list.create_ellipse_filled(x, VIEWPORT_H - y, radius * 2, radius * 2,
                                         (r, g, b, a), num_segments=segments)
    return batch.add_shape(c)


def add_border(batch, x, y, w, h, color=(0, 0, 0, 255), thickness=1, group=None):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    s = shape_list.create_rectangle_outline(x + w / 2, _gl_y_top(y, h), w, h,
                                            (r, g, b, a), border_width=thickness)
    return batch.add_shape(s)


def add_text(batch, text, x, y, size=12, color=(255, 255, 255),
             anchor_x="center", anchor_y="center", font_name=None, group=None):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b = color
        a = 255
    lbl = Text(
        text,
        x,
        VIEWPORT_H - y,
        (r, g, b, a),
        font_size=size,
        font_name=font_name or "Microsoft YaHei",  # 中文保险
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )
    return batch.add_text(lbl)


def draw_panel(batch, x, y, w, h, bg=(20, 20, 30, 235), border=(0, 0, 0, 255)):
    add_rect(batch, x, y, w, h, bg)
    add_border(batch, x, y, w, h, border, thickness=1)
