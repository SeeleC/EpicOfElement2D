# -*- coding: utf-8 -*-
"""商店窗（shop.py）：购买 / 出售 双标签页。"""

import pygame

from config import make_font
from utils import draw_text
from ui.theme import THEME
from ui.widgets import draw_panel, draw_item_icon, RARITY_COLORS


class ShopWindow:
    def __init__(self, sys):
        self.sys = sys
        self.tab = "buy"        # buy / sell
        self.selected = 0
        self.font = make_font(16)
        self.title = make_font(20, bold=True)

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if not self.sys.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.sys.close()
                return True
            if event.key == pygame.K_TAB:
                self.tab = "sell" if self.tab == "buy" else "buy"
                self.selected = 0
            if event.key == pygame.K_UP:
                self.selected = max(0, self.selected - 1)
            if event.key == pygame.K_DOWN:
                self.selected += 1
            if event.key == pygame.K_RETURN:
                self._do_action(self.selected)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self._rows()):
                if rect.collidepoint(event.pos):
                    self.selected = idx
                    self._do_action(idx)
                    return True
        return False

    def _rows(self):
        y0 = 150
        rows = []
        for i in range(min(8, self._count())):
            rows.append(pygame.Rect(180, y0 + i * 48, 640, 40))
        return rows

    def _count(self):
        return len(self._items())

    def _items(self):
        if self.tab == "buy":
            return [item for item, _price in self.sys.listing()]
        return [get_item(s["id"]) for s in self.sys.inventory.player.inventory
                if get_item(s["id"])]

    def _do_action(self, index):
        if self.tab == "buy":
            items = self.sys.listing()
            if 0 <= index < len(items):
                item, price = items[index]
                self.sys.buy(item["id"], 1)
        else:
            inv = self.sys.inventory
            if 0 <= index < len(inv.player.inventory):
                self.sys.sell(index, 1)

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.sys.is_open:
            return
        draw_panel(surface, (120, 60, 800, 620), fill=THEME["panel"],
                   border=THEME["border"], radius=12)
        draw_text(surface, f"{self.sys.npc.name} 的商店",
                  self.title, THEME["accent"], (200, 85), anchor="topleft")
        draw_text(surface, f"金币：{self.sys.player.gold} G", self.font,
                  THEME["gold"], (880, 85), anchor="topright")

        # 标签
        draw_text(surface, "购买", self.font,
                  THEME["accent"] if self.tab == "buy" else THEME["muted"],
                  (300, 120), anchor="topleft")
        draw_text(surface, "出售", self.font,
                  THEME["accent"] if self.tab == "sell" else THEME["muted"],
                  (380, 120), anchor="topleft")
        draw_text(surface, "Tab 切换 · 回车交易 · Esc 关闭", self.font,
                  THEME["muted"], (860, 650), anchor="bottomright")

        y = 150
        if self.tab == "buy":
            for i, (item, price) in enumerate(self.sys.listing()[:8]):
                self._row(surface, y, item, f"买 {price} G", i)
                y += 48
        else:
            inv = self.sys.inventory.player.inventory
            for i, slot in enumerate(inv[:8]):
                item = get_item(slot["id"])
                if not item:
                    continue
                self._row(surface, y, item, f"卖 {self.sys.sell_price(item)} G", i)
                y += 48

    def _row(self, surface, y, item, price_text, index):
        rect = pygame.Rect(180, y, 640, 40)
        if index == self.selected:
            draw_panel(surface, rect, fill=THEME["panel_light"],
                       border=THEME["accent"], radius=6)
        else:
            draw_panel(surface, rect, fill=(30, 34, 46),
                       border=THEME["border"], radius=6)
        draw_item_icon(surface, item, pygame.Rect(rect.x + 4, rect.y + 4,
                                                  32, 32))
        draw_text(surface, item["name"], self.font, THEME["text"],
                  (rect.x + 46, rect.centery), anchor="midleft")
        draw_text(surface, price_text, self.font,
                  THEME["gold"] if "买" in price_text else THEME["exp"],
                  (rect.right - 12, rect.centery), anchor="midright")
        rcol = RARITY_COLORS.get(item["rarity"], (200, 200, 200))
        draw_text(surface, item["rarity"], make_font(13), rcol,
                  (rect.right - 140, rect.centery), anchor="midright")


def get_item(item_id):
    from data.items import get_item as _gi
    return _gi(item_id)