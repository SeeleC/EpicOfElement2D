# -*- coding: utf-8 -*-
"""
基础控件（widgets.py）
======================
面板 / 按钮 / 进度条 / 文本换行 / 占位物品图标。
全部基于纯几何绘制，无外部美术资源。
"""

import pygame

from config import make_font
from utils import draw_text
from ui.theme import THEME

RARITY_COLORS = {
    "common":    (180, 190, 200),
    "uncommon":  (90, 200, 120),
    "rare":      (90, 160, 255),
    "epic":      (200, 130, 255),
    "legendary": (255, 190, 60),
}


def draw_panel(surface, rect, fill=None, border=None, radius=8, alpha=220):
    fill = fill or THEME["panel"]
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*fill, alpha), s.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(s, (*border, alpha), s.get_rect(), width=2,
                         border_radius=radius)
    surface.blit(s, rect.topleft)


def wrap_text(text, font, max_width):
    """按像素宽度自动换行。"""
    lines = []
    for raw in str(text).split("\n"):
        cur = ""
        for ch in raw:
            if font.size(cur + ch)[0] > max_width:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
    return lines


def draw_item_icon(surface, item, rect):
    """无美术资源时的占位图标：稀有度描边 + 名称首字。"""
    rect = pygame.Rect(rect)
    color = RARITY_COLORS.get(item["rarity"], (200, 200, 200))
    pygame.draw.rect(surface, (20, 22, 30), rect, border_radius=4)
    pygame.draw.rect(surface, color, rect, width=2, border_radius=4)
    font = make_font(max(12, int(rect.h * 0.5)), bold=True)
    draw_text(surface, item["name"][:1], font, color,
              rect.center, anchor="center")


class Button:
    def __init__(self, rect, text, on_click=None, font=None,
                 base=None, hover=None, key=None, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.font = font or make_font(18)
        self.base = base or THEME["panel_light"]
        self.hover = hover or THEME["border_light"]
        self.key = key
        self.enabled = enabled

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        if event.type == pygame.KEYDOWN and self.key is not None \
                and event.key == self.key:
            if self.on_click:
                self.on_click()
            return True
        return False

    def draw(self, surface, mouse_pos=None):
        mouse_pos = mouse_pos or pygame.mouse.get_pos()
        if not self.enabled:
            col = (28, 32, 42)
        elif self.rect.collidepoint(mouse_pos):
            col = self.hover
        else:
            col = self.base
        draw_panel(surface, self.rect, fill=col, border=THEME["border"],
                   radius=6)
        draw_text(surface, self.text, self.font,
                  THEME["text"] if self.enabled else THEME["muted"],
                  self.rect.center, anchor="center")


class ProgressBar:
    def __init__(self, rect, ratio, color, bg=None, border=True):
        self.rect = pygame.Rect(rect)
        self.ratio = max(0.0, min(1.0, ratio))
        self.color = color
        self.bg = bg or THEME["panel_light"]
        self.border = border

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg, self.rect, border_radius=3)
        if self.ratio > 0:
            w = max(2, int(self.rect.w * self.ratio))
            pygame.draw.rect(surface, self.color,
                             (self.rect.x, self.rect.y, w, self.rect.h),
                             border_radius=3)
        if self.border:
            pygame.draw.rect(surface, THEME["border"], self.rect,
                             width=1, border_radius=3)