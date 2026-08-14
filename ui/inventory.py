# -*- coding: utf-8 -*-
"""
背包 / 装备面板（inventory.py）
===============================
左侧装备栏（6 槽），右侧背包网格（10×6）。
左键选中，回车/右键使用或装备，U 卸下，Esc 关闭，显示物品悬浮信息。
"""

import pygame

from config import make_font
from utils import draw_text
from data.items import get_item
from ui.theme import THEME
from ui.widgets import draw_panel, draw_item_icon, RARITY_COLORS
from systems.equipment import SLOT_LABELS


class InventoryPanel:
    def __init__(self, inv, equip):
        self.inv = inv
        self.equip = equip
        self.selected = None       # ("inv", index) / ("equip", slot)
        self.font = make_font(15)
        self.title = make_font(20, bold=True)
        self.tooltip_item = None

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            if event.key == pygame.K_RETURN:
                self._activate()
            if event.key == pygame.K_u:
                if self.selected and self.selected[0] == "equip":
                    self.equip.unequip(self.selected[1])
                    self.selected = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._select_at(event.pos)
        if event.type == pygame.MOUSEMOTION:
            self._hover_at(event.pos)
        return None

    def _select_at(self, pos):
        self.selected = None
        for slot, rect in self._equip_rects().items():
            if rect.collidepoint(pos):
                self.selected = ("equip", slot)
                return
        for i, rect in enumerate(self._grid_rects()):
            if rect.collidepoint(pos):
                self.selected = ("inv", i)
                return

    def _hover_at(self, pos):
        self.tooltip_item = None
        for slot, rect in self._equip_rects().items():
            if rect.collidepoint(pos):
                item = self.equip.slot_item(slot)
                self.tooltip_item = item
                return
        for i, rect in enumerate(self._grid_rects()):
            if rect.collidepoint(pos):
                inv = self.inv.player.inventory
                if i < len(inv):
                    self.tooltip_item = get_item(inv[i]["id"])
                return

    def _activate(self):
        if not self.selected:
            return
        kind, key = self.selected
        if kind == "inv":
            inv = self.inv.player.inventory
            if 0 <= key < len(inv):
                item = get_item(inv[key]["id"])
                if not item:
                    return
                if item["usable"]:
                    self.inv.use_at(key)
                elif item.get("slot"):
                    self.equip.equip(item["id"])
        elif kind == "equip":
            self.equip.unequip(key)
        self.selected = None

    # ------------------------------------------------------------------
    def _equip_rects(self):
        x, y = 180, 120
        return {slot: pygame.Rect(x, y + i * 60, 200, 52)
                for i, slot in enumerate(SLOT_ORDER)}

    def _grid_rects(self):
        x0, y0 = 420, 120
        cell, gap = 46, 6
        rects = []
        for i in range(60):
            col, row = i % 10, i // 10
            rects.append(pygame.Rect(x0 + col * (cell + gap),
                                     y0 + row * (cell + gap), cell, cell))
        return rects

    # ------------------------------------------------------------------
    def draw(self, surface):
        draw_panel(surface, (120, 60, 880, 660), fill=THEME["panel"],
                   border=THEME["border"], radius=12)
        draw_text(surface, "背包 / 装备", self.title, THEME["accent"],
                  (160, 80), anchor="topleft")
        draw_text(surface, "左键选择 · 回车 使用/装备 · U 卸下 · Esc 关闭",
                  self.font, THEME["muted"], (960, 690), anchor="bottomright")

        # 装备栏
        for slot in SLOT_ORDER:
            rect = self._equip_rects()[slot]
            item = self.equip.slot_item(slot)
            sel = (self.selected == ("equip", slot))
            draw_panel(surface, rect, fill=THEME["panel_light"]
                       if sel else (30, 34, 46),
                       border=THEME["accent"] if sel else THEME["border"],
                       radius=6)
            draw_text(surface, SLOT_LABELS[slot], self.font, THEME["muted"],
                      (rect.x + 8, rect.centery), anchor="midleft")
            if item:
                draw_item_icon(surface, item,
                               pygame.Rect(rect.right - 44, rect.y + 6,
                                           40, 40))
                draw_text(surface, item["name"], self.font, THEME["text"],
                          (rect.x + 78, rect.centery), anchor="midleft")

        # 背包网格
        inv = self.inv.player.inventory
        for i, rect in enumerate(self._grid_rects()):
            draw_panel(surface, rect, fill=(26, 30, 40),
                       border=THEME["border"], radius=4)
            if i < len(inv):
                item = get_item(inv[i]["id"])
                if item:
                    draw_item_icon(surface, item, rect.inflate(-6, -6))
                draw_text(surface, f"{inv[i]['count']}", self.font,
                          THEME["text"], (rect.right - 2, rect.bottom - 2),
                          anchor="bottomright", shadow=True)

        # 悬浮信息
        if self.tooltip_item:
            self._tooltip(surface, self.tooltip_item)

    def _tooltip(self, surface, item):
        lines = [item["name"], f"稀有度：{item['rarity']}",
                 item["desc"]]
        for k, v in (item.get("stats") or {}).items():
            lines.append(f"  +{v} {k}")
        font = make_font(15)
        w = max(240, max(font.size(l)[0] for l in lines) + 30)
        h = 26 * len(lines) + 20
        x, y = 180, 120
        draw_panel(surface, (x, y, w, h), fill=(24, 28, 40),
                   border=RARITY_COLORS.get(item["rarity"], (200, 200, 200)),
                   radius=8)
        ty = y + 12
        for i, ln in enumerate(lines):
            col = RARITY_COLORS.get(item["rarity"], THEME["text"]) if i == 0 \
                else THEME["text"]
            draw_text(surface, ln, font, col, (x + 14, ty),
                      anchor="topleft")
            ty += 26