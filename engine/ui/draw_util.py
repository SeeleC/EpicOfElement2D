# -*- coding: utf-8 -*-
"""UI 绘制工具：与 batch 协作的形状与文字基元。

坐标约定（全项目统一）：**屏幕左上角为原点，X 向右、Y 向下为正**（见 config 注释）。
而 pyglet 2.x 的 shapes / text.Label 默认采用「左下角为原点、Y 向上」的 OpenGL 坐标。
因此本模块在把每个基元的坐标传给 pyglet 前做一次垂直翻转（水平方向不变）：

    GL_y = VIEWPORT_H - y          （circle / 文本锚点）
    GL_y = VIEWPORT_H - y - h      （矩形 / 边框矩形，y 为其顶边）

调用方无需关心此差异，只需按「左上原点、Y 向下」传参即可。
窗口高度由 Game 在每帧 render 前通过 set_viewport_h() 提供。
"""
import pyglet
from pyglet import shapes, text as pyglet_text
from .. import config

# ---------------------------------------------------------------------------
# 关键保活机制：
# pyglet 2.1.x 的 shapes / text.Label 在创建后必须被强引用，否则会被 GC 回收，
# 导致 batch.draw() 画不出任何内容（窗口黑屏）。
#
# 这里把「当前帧创建的全部基元」收集到 _FRAME 列表强引用保活；Game 在每帧
# 渲染前调用 begin_frame() 清空上一帧引用并开始收集新一帧。这样：
#   - 绘制期间基元被强引用、不被 GC，batch.draw() 一定能画出来；
#   - 每帧对象在下一帧渲染前被及时释放，不会累积。
#
# 注意：刻意**不**采用「以 batch 为 key 的 WeakKeyDictionary」，因为 shape
# 内部会强引用所在 batch，形成循环引用，导致 batch 永不回收、条目永不清理、
# 内存无限增长——这正是早期运行几分钟后内存飙到数 GB、CPU/GC 压力骤增的根因。
# ---------------------------------------------------------------------------

# 当前视口高度（由调用方每帧 render 前设置）。把「左上、Y 向下」坐标
# 翻转成 pyglet shapes 的「左下、Y 向上」坐标。
VIEWPORT_H = 0

# “当前帧所有基元”的强引用列表：保活本帧创建的 shapes / Label，防止被 GC。
_FRAME = []


def set_viewport_h(h):
    global VIEWPORT_H
    VIEWPORT_H = h


def begin_frame():
    """清空上一帧基元引用并开始收集本帧。应在每帧渲染前调用。"""
    _FRAME.clear()


def _gl_y_top(y, h=0):
    """矩形顶边 y（左上原点 Y 向下）-> GL 左下原点 Y 向上 的矩形底边 y。"""
    return VIEWPORT_H - y - h


def _retain(batch, obj):
    """登记基元到当前帧列表，保持强引用防止 GC（batch 仅作签名兼容）。"""
    _FRAME.append(obj)
    return obj


def add_rect(batch, x, y, w, h, color, group=None):
    """向 batch 添加一个矩形。y 为其顶边（左上原点 Y 向下）。"""
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    s = shapes.Rectangle(x, _gl_y_top(y, h), w, h, color=(r, g, b),
                         batch=batch, group=group)
    s.opacity = a
    return _retain(batch, s)


def add_circle(batch, x, y, radius, color, group=None, segments=24):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    c = shapes.Circle(x, VIEWPORT_H - y, radius, color=(r, g, b),
                      batch=batch, group=group, segments=segments)
    c.opacity = a
    return _retain(batch, c)


def add_border(batch, x, y, w, h, color=(0, 0, 0, 255), thickness=1, group=None):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    s = shapes.BorderedRectangle(x, _gl_y_top(y, h), w, h, border=thickness,
                                 color=(r, g, b), border_color=(r, g, b),
                                 batch=batch, group=group)
    return _retain(batch, s)


def add_text(batch, text, x, y, size=12, color=(255, 255, 255),
             anchor_x="center", anchor_y="center", font_name=None, group=None):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b = color
        a = 255
    try:
        lbl = pyglet_text.Label(
            text, font_name=font_name, font_size=size,
            color=(r, g, b, a), batch=batch, group=group,
            anchor_x=anchor_x, anchor_y=anchor_y,
            x=x, y=VIEWPORT_H - y,
        )
    except TypeError:
        lbl = pyglet.text.Label(
            text, font_size=size, color=(r, g, b, a),
            batch=batch, group=group, anchor_x=anchor_x, anchor_y=anchor_y,
            x=x, y=VIEWPORT_H - y,
        )
    return _retain(batch, lbl)


def draw_panel(batch, x, y, w, h, bg=(20, 20, 30, 235), border=(0, 0, 0, 255)):
    add_rect(batch, x, y, w, h, bg)
    add_border(batch, x, y, w, h, border, thickness=1)
