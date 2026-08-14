# -*- coding: utf-8 -*-
"""
《元素之诗：灾厄》2D 版 —— 通用工具函数（utils.py）
====================================================
提供所有模块共用的小工具：数学、矩形碰撞、文本换行/绘制、
数字格式化、加权随机、图片加载（缺失时自动生成占位图）、
颜色变换等。

依赖：config（常量/路径）+ pygame。兼容 Python 3.9。
"""

import math
import os
import random

import pygame

from config import IMG_DIR
from text import draw_text as _engine_draw_text


# ---------------------------------------------------------------------------
# 数学工具
# ---------------------------------------------------------------------------
def clamp(value, lo, hi):
    """把数值限制在 [lo, hi] 区间。"""
    return max(lo, min(hi, value))


def lerp(a, b, t):
    """线性插值。"""
    return a + (b - a) * t


def smooth_step(t):
    """平滑插值曲线（0~1 之间平滑过渡）。"""
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


def angle_to(x1, y1, x2, y2):
    """返回从点1指向点2的角度（弧度）。"""
    return math.atan2(y2 - y1, x2 - x1)


def move_towards(current, target, max_delta):
    """以不超过 max_delta 的速度逼近目标值。"""
    if abs(target - current) <= max_delta:
        return target
    return current + math.copysign(max_delta, target - current)


# ---------------------------------------------------------------------------
# 矩形 / 碰撞
# ---------------------------------------------------------------------------
def point_in_rect(px, py, rect):
    return rect.collidepoint(px, py)


def rects_collide(rect_a, rect_b):
    return rect_a.colliderect(rect_b)


def rect_intersection(rect_a, rect_b):
    """返回两个矩形的交集（pygame.Rect），不相交时返回 None。"""
    x = max(rect_a.left, rect_b.left)
    y = max(rect_a.top, rect_b.top)
    w = min(rect_a.right, rect_b.right) - x
    h = min(rect_a.bottom, rect_b.bottom) - y
    if w <= 0 or h <= 0:
        return None
    return pygame.Rect(x, y, w, h)


# ---------------------------------------------------------------------------
# 文本
# ---------------------------------------------------------------------------
def wrap_text(text, font, max_width):
    """按像素宽度换行（支持中文，无空格也能正确断行）。"""
    lines = []
    for raw in str(text).split("\n"):
        line = ""
        for ch in raw:
            test = line + ch
            if font.size(test)[0] > max_width and line:
                lines.append(line)
                line = ch
            else:
                line = test
        lines.append(line)
    return lines


def draw_text(surface, text, font, color, pos, anchor="topleft",
              shadow=False, alpha=255, aa=True):
    return _engine_draw_text(surface, text, font, color, pos,
                             anchor=anchor, shadow=shadow,
                             alpha=alpha, aa=aa)


def draw_wrapped(surface, text, font, color, rect, line_spacing=4,
                 anchor="topleft"):
    """在给定区域内绘制自动换行文本，返回已绘制的总行数。"""
    lines = wrap_text(text, font, rect.width)
    y = rect.top
    for line in lines:
        draw_text(surface, line, font, color, (rect.left, y), anchor=anchor)
        y += font.get_linesize() + line_spacing
    return len(lines)


# ---------------------------------------------------------------------------
# 数字格式化
# ---------------------------------------------------------------------------
def format_number(n):
    """把数字格式化为中文习惯（1.2万 / 3.45亿）。"""
    n = int(n)
    if abs(n) >= 100000000:
        return f"{n / 100000000:.2f}亿"
    if abs(n) >= 10000:
        return f"{n / 10000:.1f}万"
    return str(n)


# ---------------------------------------------------------------------------
# 随机
# ---------------------------------------------------------------------------
def weighted_choice(pairs):
    """按权重随机选择。pairs: [(item, weight), ...]，返回 item 或 None。"""
    total = sum(w for _, w in pairs)
    if total <= 0:
        return None
    r = random.uniform(0, total)
    upto = 0.0
    for item, w in pairs:
        upto += w
        if r <= upto:
            return item
    return pairs[-1][0] if pairs else None


# ---------------------------------------------------------------------------
# 图片 / 表面
# ---------------------------------------------------------------------------
def make_surface(size, color, radius=0, border=0, border_color=None):
    """创建一个纯色（可带圆角/描边）的表面。"""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    rect = surf.get_rect()
    if radius:
        pygame.draw.rect(surf, color, rect, border_radius=radius)
    else:
        surf.fill(color)
    if border:
        pygame.draw.rect(surf, border_color or color, rect, border,
                         border_radius=radius)
    return surf


def load_image(name, scale=None, colorkey=None, default_color=(140, 140, 200),
               default_size=(48, 48)):
    """加载 IMG_DIR 下的图片；文件不存在时生成占位图，保证不崩溃。"""
    path = os.path.join(IMG_DIR, name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
    else:
        img = make_surface(default_size, default_color)
    if scale is not None:
        img = pygame.transform.scale(img, scale)
    if colorkey is not None:
        img.set_colorkey(colorkey)
    return img


def tint_surface(surface, color):
    """把表面整体染成指定颜色（乘法混合，白=原样）。"""
    result = surface.copy()
    overlay = pygame.Surface(result.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, 255))
    result.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result


def flash_white(surface, amount=1.0):
    """为表面叠加白色闪光（受击闪白效果用）。amount: 0~1。"""
    result = surface.copy()
    overlay = pygame.Surface(result.get_size(), pygame.SRCALPHA)
    v = int(255 * clamp(amount, 0, 1))
    overlay.fill((v, v, v, v))
    result.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return result


def flip_frames(frames, flip_x=True):
    """把一列帧水平/垂直翻转，用于角色朝向。"""
    return [pygame.transform.flip(f, flip_x, False) for f in frames]


if __name__ == "__main__":
    # 自检
    print("wrap_text:", wrap_text("元素之诗灾厄是一部很好玩的ARPG地图", None, 10)[:2])
    print("format_number(123456) =", format_number(123456))
    print("clamp(15,0,10) =", clamp(15, 0, 10))