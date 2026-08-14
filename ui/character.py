# -*- coding: utf-8 -*-
"""角色面板（character.py）：六维属性 + 自由点数分配。"""

import pygame

from config import make_font
from utils import draw_text
from ui.theme import THEME
from ui.widgets import draw_panel, ProgressBar
from systems.level_up import ALLOC_STATS, STAT_LABELS


class CharacterPanel:
    def __init__(self, level_sys):
        self.level_sys = level_sys
        self.font = make_font(17)
        self.title = make_font(22, bold=True)

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            if event.key == pygame.K_a:
                self.level_sys.auto_allocate(self._player)
                return "alloc"
            idx = event.key - pygame.K_1
            if 0 <= idx < len(ALLOC_STATS):
                self.level_sys.allocate(self._player, ALLOC_STATS[idx])
                return "alloc"
        return None

    def draw(self, surface, player):
        self._player = player
        draw_panel(surface, (280, 120, 560, 480), fill=THEME["panel"],
                   border=THEME["border"], radius=12)
        draw_text(surface, "角色信息", self.title, THEME["accent"],
                  (320, 140), anchor="topleft")
        draw_text(surface, f"{player.class_name} · Lv.{player.level}",
                  self.font, THEME["text"], (320, 180), anchor="topleft")
        draw_text(surface, f"经验：{player.exp} / {player.gold} G",
                  self.font, THEME["muted"], (320, 210), anchor="topleft")

        # 自由点数
        draw_text(surface, f"可用点数：{player.free_points}",
                  make_font(18, bold=True),
                  THEME["accent"] if player.free_points > 0 else THEME["muted"],
                  (760, 140), anchor="topright")

        y = 260
        for i, key in enumerate(ALLOC_STATS):
            rect = pygame.Rect(320, y, 480, 40)
            draw_panel(surface, rect, fill=(30, 34, 46),
                       border=THEME["border"], radius=6)
            draw_text(surface, f"{i + 1}  {STAT_LABELS[key]}",
                      self.font, THEME["text"], (rect.x + 14, rect.centery),
                      anchor="midleft")
            val = player.get_stat(key)
            draw_text(surface, f"{val:.0f}", self.font, THEME["accent"],
                      (rect.right - 90, rect.centery), anchor="midright")
            if key == "crit":
                draw_text(surface, f"{(val * 100):.0f}%", self.font,
                          THEME["text"], (rect.right - 14, rect.centery),
                          anchor="midright")
            y += 48
        draw_text(surface, "按 1~6 加点 · A 一键加点 · Esc 关闭",
                  self.font, THEME["muted"], (320, y + 14), anchor="topleft")