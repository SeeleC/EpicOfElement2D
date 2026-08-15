# -*- coding: utf-8 -*-
"""UI 绘制工具：与 batch 协作的形状与文字基元。"""
import weakref

import pyglet
from pyglet import shapes, text as pyglet_text
from .. import config

# ---------------------------------------------------------------------------
# 关键保活机制：
# pyglet 2.1.x 的 shapes / text.Label 在创建后必须被强引用，否则会被垃圾回收，
# 导致 batch.draw() 画不出任何内容（窗口黑屏）。
# 这里用 WeakKeyDictionary 以 batch 为 key，把每次创建的基元强引用保留：
#   - batch 存活期间，其全部基元对象都被本表强引用，不会被 GC；
#   - batch 一旦不再被引用（如每帧重建的新 batch 覆盖旧 batch），该条目自动清除，不泄漏。
# 因此所有 add_* 的调用方无需改动即可自动获得正确的引用保活。
# ---------------------------------------------------------------------------
_KEEP = weakref.WeakKeyDictionary()


def _retain(batch, obj):
    """把创建的基元对象登记到所属 batch 名下，保持强引用防止 GC。"""
    lst = _KEEP.get(batch)
    if lst is None:
        lst = []
        _KEEP[batch] = lst
    lst.append(obj)
    return obj


def add_rect(batch, x, y, w, h, color, group=None):
    """向 batch 添加一个矩形。返回 shape（并被 batch 强引用保活）。"""
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    s = shapes.Rectangle(x, y, w, h, color=(r, g, b), batch=batch, group=group)
    s.opacity = a
    return _retain(batch, s)


def add_circle(batch, x, y, radius, color, group=None, segments=24):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    c = shapes.Circle(x, y, radius, color=(r, g, b), batch=batch,
                      group=group, segments=segments)
    c.opacity = a
    return _retain(batch, c)


def add_border(batch, x, y, w, h, color=(0, 0, 0, 255), thickness=1, group=None):
    if isinstance(color, tuple) and len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b, a = (*color, 255)
    s = shapes.BorderedRectangle(x, y, w, h, border=thickness,
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
            anchor_x=anchor_x, anchor_y=anchor_y, x=x, y=y,
        )
    except TypeError:
        lbl = pyglet.text.Label(
            text, font_size=size, color=(r, g, b, a),
            batch=batch, group=group, anchor_x=anchor_x, anchor_y=anchor_y,
            x=x, y=y,
        )
    return _retain(batch, lbl)


def draw_panel(batch, x, y, w, h, bg=(20, 20, 30, 235), border=(0, 0, 0, 255)):
    add_rect(batch, x, y, w, h, bg)
    add_border(batch, x, y, w, h, border, thickness=1)
