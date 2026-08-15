# -*- coding: utf-8 -*-
"""对话 / NPC 交互界面。"""
from . import draw_util
from .. import config


class DialogBox:
    """底部对话框：显示 NPC 话语。按 E 推进 / 关闭。"""

    def __init__(self, npc=None):
        self.npc = npc
        self.text = ""
        self.open = False

    def show(self, npc):
        self.npc = npc
        self.text = npc.greet() if npc else ""
        self.open = True

    def draw(self, batch, win_w, win_h):
        if not self.open:
            return
        h = 90
        x, y = 20, 20
        w = win_w - 40
        draw_util.add_rect(batch, x, y, w, h, (12, 12, 20, 235))
        draw_util.add_border(batch, x, y, w, h, (200, 200, 200, 80))
        draw_util.add_text(batch, (self.npc.name if self.npc else "?"),
                           x + 12, y + h - 8, size=14, anchor_x="left",
                           anchor_y="top", color=(240, 200, 90))
        draw_util.add_text(batch, self.text, x + 12, y + h - 32, size=13,
                           anchor_x="left", anchor_y="top", color=(230, 230, 230))
        draw_util.add_text(batch, "[E] 继续 / 关闭",
                           x + w - 10, y + 8, size=11, anchor_x="right",
                           color=(150, 150, 160))
