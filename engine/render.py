# -*- coding: utf-8 -*-
"""程序化渲染辅助。

在没有美术贴图的情况下，用 pyglet shapes / 基本几何图形
绘制「饥荒式」的俯视角色、怪物、图标与 UI。

- draw_rect, draw_circle, draw_poly 为世界/UI 通用绘制。
- 图标用简单像素风格：每个图标由若干色块构成。
"""
import pyglet
from . import config


def rect(x, y, w, h, color=(200, 200, 200), group=None):
    """绘制填充矩形（屏幕像素坐标）。返回 shape 以便释放。"""
    return pyglet.shapes.Rectangle(x, y, w, h, color=color, batch=None)


def circle(x, y, r, color=(200, 200, 200), segments=None):
    return pyglet.shapes.Circle(x, y, r, color=color, segments=segments if segments else 24)


def draw_centered_text(text, cx, cy, font_size=14, color=(255, 255, 255),
                       anchor_x="center", anchor_y="center", bold=False):
    return pyglet.text.Label(
        text, font_size=font_size, color=(*color, 255),
        bold=bold, anchor_x=anchor_x, anchor_y=anchor_y,
        x=cx, y=cy,
    )


# ---------------------------------------------------------------------------
# 图标绘制器 —— 每个物品 id 对应一张「像素色块图」
# 由引擎的 IconCache 统一渲染成贴图，避免每帧重绘。
# ---------------------------------------------------------------------------
# 简单的 8x8 彩色矩阵（用字符代表颜色），用于程序化生成图标。
_ICON_IMAGES = {
    "coin": {
        "palette": {"G": (235, 200, 80), "D": (180, 140, 40)},
        "map": [
            "........", "..GGGG..", ".GGGGGG.", "GGGGGGGG",
            "GGGGGGGG", ".GGGGGG.", "..GGGG..", "........",
        ],
    },
    "sword": {
        "palette": {"S": (210, 210, 215), "H": (170, 110, 60), "G": (240, 210, 90)},
        "map": [
            "S.......", ".S......", ".S......", "..S.....",
            "..S....H", "..HGGH..", "...H....", "........",
        ],
    },
    "bow": {
        "palette": {"B": (160, 110, 60), "T": (230, 230, 230)},
        "map": [
            "B.......", "B.B.....", "B..B....", "B...B...",
            "B....B..", "B.....B.", "B......T", "........",
        ],
    },
    "shield": {
        "palette": {"S": (120, 150, 200), "E": (190, 200, 220), "R": (220, 220, 230)},
        "map": [
            ".S....S.", ".SS..SS.", "SSSSSSSS", "SSSSSSSS",
            "RRRRRRRR", ".RRRRRR.", "..RRRR..", "...RR...",
        ],
    },
    "staff": {
        "palette": {"S": (150, 110, 70), "T": (80, 160, 255)},
        "map": [
            "......T.", ".....T..", "....S...", "...S....",
            "..S.....", ".S......", "S.......", "........",
        ],
    },
    "potion": {
        "palette": {"B": (220, 60, 60), "N": (200, 200, 200), "R": (240, 240, 240)},
        "map": [
            "...NN...", "...NN...", "..BBBB..", ".BBBBBB.",
            ".BBBBBB.", ".BBBBBB.", ".BBBBBB.", "..BBBB..",
        ],
    },
    "food": {
        "palette": {"B": (220, 180, 100), "T": (170, 120, 60)},
        "map": [
            "........", "........", "..BBBB..", ".BBBBBB.",
            ".BBBBBB.", "..BBBB..", "........", "........",
        ],
    },
    "meat": {
        "palette": {"M": (200, 80, 80), "F": (240, 200, 180)},
        "map": [
            "........", ".MMMM...", "MMMMMM..", "FFFFFFF.",
            "FFFFFFF.", ".FFFFFF.", "..FFFF..", "........",
        ],
    },
    "axe": {
        "palette": {"W": (130, 80, 50), "M": (190, 190, 195)},
        "map": [
            ".M......", ".M......", ".M......", ".M...WW.",
            ".M..WW..", ".MMMM...", "..MM....", "........",
        ],
    },
    "pick": {
        "palette": {"W": (130, 80, 50), "M": (180, 180, 185)},
        "map": [
            "........", "MMM....W", ".MM...W.", "..MM.W..", "...MW...",
            ".....W..", "........", "........",
        ],
    },
    "sickle": {
        "palette": {"W": (130, 80, 50), "M": (200, 200, 205)},
        "map": [
            "........", "........", ".MMM....", "M...M...",
            "M...M...", ".MMM..W.", ".....W..", "........",
        ],
    },
    "ore": {
        "palette": {"O": (110, 110, 115), "H": (180, 180, 185)},
        "map": [
            "........", "..OOOO..", ".OOOOOO.", ".OHHOOH.",
            ".OOOOHO.", ".OOOOOO.", "..OOOO..", "........",
        ],
    },
    "log": {
        "palette": {"W": (140, 95, 55), "R": (100, 65, 38)},
        "map": [
            "..WWWW..", ".WWWWWW.", ".WWRRWW.", ".WRR RWW".replace(" ", ""),
            ".WWRRWW.", ".WWWWWW.", ".WWWWWW.", "..WWWW..",
        ],
    },
    "hide": {
        "palette": {"H": (160, 130, 90)},
        "map": [
            "........", "........", ".HHHHHH.", ".HHHHHH.",
            ".HHHHHH.", ".HHHHHH.", ".HHHHHH.", "........",
        ],
    },
    "tusk": {
        "palette": {"T": (230, 230, 230)},
        "map": [
            "........", "........", "..T.....", "...T....",
            "....T...", "....T...", "....T...", "........",
        ],
    },
    "slime": {
        "palette": {"S": (70, 160, 80), "E": (40, 120, 50)},
        "map": [
            "........", ".SSSS...", "SSSSSS..", "SSSSSS..",
            "EEEEEE..", ".SSSS...", "........", "........",
        ],
    },
    "ingot": {
        "palette": {"I": (200, 200, 205)},
        "map": [
            "........", "........", ".IIIIII.", ".IIIIII.",
            "..IIII..", "..IIII..", "...II...", "........",
        ],
    },
    "herb": {
        "palette": {"G": (90, 170, 80), "F": (220, 120, 160)},
        "map": [
            "...G....", "..GGG...", ".GGGGG..", ".....F..",
            "........", "........", "........", "........",
        ],
    },
    "crop": {
        "palette": {"G": (180, 170, 50), "S": (90, 170, 70)},
        "map": [
            "..SSSS..", ".SSSSSS.", ".SSSSSS.", ".GGGGGG.",
            ".GGGGGG.", ".GGGGGG.", ".GGGGGG.", "........",
        ],
    },
    # 怪物图标
    "boar": {
        "palette": {"B": (150, 110, 80), "E": (80, 60, 40), "W": (230, 230, 230)},
        "map": [
            ".W....W.", ".BBBBBB.", "BBBBBBBB", "BBEBEBBB",
            "BBBBBBBB", "BWBWBWBW", "BBBBBBBB", "........",
        ],
    },
    "rock_beast": {
        "palette": {"R": (120, 120, 125), "D": (80, 80, 85), "E": (220, 60, 40)},
        "map": [
            "........", "..RRRR..", ".RRRRRR.", ".RREERR.",
            ".RRRRRR.", "RRRRRRRR", "RRDDDDRR", "........",
        ],
    },
    "slime": {
        "palette": {"S": (80, 160, 90), "E": (40, 120, 50)},
        "map": [
            "........", ".SSSS...", "SSSSSS..", "SSESSS..",
            "SSSSSS..", "EEEEEE..", ".SSSS...", "........",
        ],
    },
    "goat": {
        "palette": {"G": (220, 220, 225), "H": (140, 140, 150)},
        "map": [
            "GH.....G", "GH.....G", ".GGGGGG.", ".GGGGGG.",
            "GGGGGGGG", ".GGGGGG.", "........", "........",
        ],
    },
}


class IconCache:
    """图标颜色缓存：返回每个图标的主色（美术可替换为真实贴图）。"""

    def __init__(self, size=None):
        self.size = size or config.ASSET_TILE
        self.cache = {}

    def color_of(self, icon_id):
        if icon_id in self.cache:
            return self.cache[icon_id]
        data = _ICON_IMAGES.get(icon_id, _ICON_IMAGES.get("coin"))
        color = (200, 200, 200)
        if data and "palette" in data:
            color = tuple(list(data["palette"].values())[0])
        self.cache[icon_id] = color
        return color


# 返回一个代表该图标的 pyglet Sprite（主色占位）
def icon_sprite(icon_id, x, y, scale=1.0, batch=None, group=None):
    """按图标 id 生成主色占位方块。"""
    base = _ICON_IMAGES.get(icon_id)
    color = (200, 200, 200)
    if base and "palette" in base:
        color = tuple(list(base["palette"].values())[0])
    size = config.ASSET_TILE * scale
    return pyglet.shapes.Rectangle(x, y, size, size, color=color, batch=batch, group=group)
