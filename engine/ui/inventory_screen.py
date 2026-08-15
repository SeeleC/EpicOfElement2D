# -*- coding: utf-8 -*-
"""背包 / 装备界面。"""
from . import draw_util
from .. import config
from .. import render as R


class InventoryScreen:
    def __init__(self, game):
        self.game = game

    def draw(self, batch):
        p = self.game.player
        w = self.game.width
        h = self.game.height

        draw_util.add_rect(batch, 0, 0, w, h, (0, 0, 0, 160))
        draw_util.add_text(batch, "背包 Inventory", w / 2, h - 40, size=20,
                           color=(255, 255, 255))
        draw_util.add_text(batch, "金币: " + str(p.inventory.gold),
                           w / 2, h - 70, size=14, color=config.Palette.GOLD)

        slot = 56
        gap = 8
        cols, rows = 6, 4
        gx, gy = w / 2 - (cols * slot + (cols - 1) * gap) / 2 - 120, h - 110
        px, py = gx, gy
        draw_util.add_text(batch, "物品栏", px, py + rows * (slot + gap) + 8,
                           size=12, anchor_x="left", color=(200, 200, 200))
        for cell in range(p.inventory.size):
            cx = cell % cols
            cy = cell // cols
            x = px + cx * (slot + gap)
            y = py + (rows - 1 - cy) * (slot + gap)
            stack = p.inventory.slots[cell]
            draw_util.add_rect(batch, x, y, slot, slot, (45, 45, 55))
            draw_util.add_border(batch, x, y, slot, slot, (10, 10, 15))
            if stack is not None:
                draw_util.add_rect(batch, x + 4, y + 4, slot - 8, slot - 8,
                                   R.IconCache().color_of(stack.base.get("icon", "coin")))
                txt = stack.base.get("name", stack.item_id)
                draw_util.add_text(batch, txt if len(txt) < 5 else txt[:4],
                                   x + slot / 2, y + slot - 10, size=9,
                                   color=(255, 255, 255))
                if stack.count > 1:
                    draw_util.add_text(batch, str(stack.count),
                                       x + slot - 6, y + 8, size=10,
                                       color=(255, 255, 255))

        ex = px + cols * (slot + gap) + 40
        draw_util.add_text(batch, "装备", ex, py + rows * (slot + gap) + 8,
                           size=12, anchor_x="left", color=(200, 200, 200))
        eq_slots = ["head", "body", "main_hand", "off_hand", "trinket"]
        eq_labels = {"head": "头部", "body": "护甲", "main_hand": "主手",
                     "off_hand": "副手", "trinket": "饰品"}
        for i, slot_name in enumerate(eq_slots):
            ey = py + (len(eq_slots) - 1 - i) * (slot + gap)
            draw_util.add_rect(batch, ex, ey, slot, slot, (35, 40, 50))
            draw_util.add_border(batch, ex, ey, slot, slot, (10, 10, 15))
            stack = p.equipment.get(slot_name)
            if stack:
                draw_util.add_rect(batch, ex + 4, ey + 4, slot - 8, slot - 8,
                                   R.IconCache().color_of(stack.base.get("icon", "coin")))
                draw_util.add_text(batch, stack.base.get("name", ""),
                                   ex + slot / 2, ey + 8, size=8,
                                   color=(255, 255, 255))
            else:
                draw_util.add_text(batch, eq_labels[slot_name],
                                   ex + slot / 2, ey + slot / 2, size=9,
                                   color=(120, 120, 130))

        draw_util.add_text(batch, "[ESC] 关闭  ·  选中的装备按 [Q] 穿戴/卸下",
                           w / 2, 15, size=11, color=(180, 180, 180))
