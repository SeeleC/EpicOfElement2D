# -*- coding: utf-8 -*-
"""
HUD（hud.py）
=============
游戏进行时的常驻界面：
  - 左下：HP / MP / EXP 条 + 等级 + 金币
  - 底部中间：药水快捷栏（pot_1~4）
  - 右下：6 技能栏（冷却遮罩 / 蓝耗不足高亮 / 快捷键）
  - 伤害飘字（世界坐标 -> 屏幕坐标）
  - 顶部：首领血条
"""

import pygame

from config import exp_for_level, make_font
from data.items import get_item
from data.skills import get_skill
from utils import draw_text
from ui.theme import THEME
from ui.widgets import ProgressBar, draw_panel, draw_item_icon


class HUD:
    def __init__(self):
        self.f = {
            13: make_font(13), 15: make_font(15), 16: make_font(16),
            18: make_font(18), 20: make_font(20, bold=True),
            24: make_font(24, bold=True),
        }

    # ------------------------------------------------------------------
    def draw(self, surface, player, combat, settings, cam=None):
        self._draw_bars(surface, player)
        self._draw_quickbar(surface, player)
        self._draw_skillbar(surface, player, settings)
        if cam:
            self._draw_damage_texts(surface, combat, cam)
        boss = getattr(player, "_hud_boss", None)
        if boss and getattr(boss, "alive", False):
            self._draw_boss_bar(surface, boss)

    def set_boss(self, boss):
        player_holder = getattr(self, "_player", None)

    # ------------------------------------------------------------------
    def _draw_bars(self, surface, player):
        bx, by = 18, surface.get_height() - 122
        hp_r = player.hp / max(1, player.max_hp)
        ProgressBar((bx, by, 220, 16), hp_r, THEME["hp"]).draw(surface)
        draw_text(surface, f"HP {player.hp}/{player.max_hp}", self.f[13],
                  THEME["text"], (bx + 110, by + 8), anchor="center",
                  shadow=True)
        mp_r = player.mp / max(1, player.max_mp)
        ProgressBar((bx, by + 20, 180, 12), mp_r, THEME["mp"]).draw(surface)
        exp_r = player.exp / max(1, exp_for_level(player.level))
        ProgressBar((bx, by + 36, 180, 8), exp_r, THEME["exp"]).draw(surface)
        draw_text(surface, f"Lv.{player.level}", self.f[20],
                  THEME["accent"], (bx + 232, by + 8), anchor="topleft")
        draw_text(surface, f"{player.gold} G", self.f[16], THEME["gold"],
                  (bx + 232, by + 34), anchor="topleft")
        draw_text(surface, player.class_name, self.f[13], THEME["muted"],
                  (bx + 232, by + 56), anchor="topleft")

    def _draw_quickbar(self, surface, player):
        size, gap = 44, 6
        total = 4 * size + 3 * gap
        x0 = (surface.get_width() - total) // 2
        y0 = surface.get_height() - size - 18
        inventory = getattr(player, "inventory", [])
        for i in range(1, 5):
            rect = pygame.Rect(x0 + (i - 1) * (size + gap), y0, size, size)
            draw_panel(surface, rect, fill=(30, 34, 46),
                       border=THEME["border"], radius=6)
            item_id = player.quick_slots.get(i)
            if item_id:
                item = get_item(item_id)
                if item:
                    draw_item_icon(surface, item, rect.inflate(-8, -8))
                    cnt = sum(s["count"] for s in inventory
                              if s["id"] == item_id)
                    draw_text(surface, f"{cnt}", self.f[13], THEME["text"],
                              (rect.right - 4, rect.bottom - 2),
                              anchor="bottomright", shadow=True)
            draw_text(surface, f"{i}", self.f[13], THEME["muted"],
                      (rect.x + 3, rect.y + 2), anchor="topleft")

    def _draw_skillbar(self, surface, player, settings):
        skills = player.skills
        if not skills:
            return
        size, gap = 52, 6
        total = len(skills) * size + (len(skills) - 1) * gap
        x0 = surface.get_width() - total - 18
        y0 = surface.get_height() - size - 18
        for i, sid in enumerate(skills):
            skill = get_skill(sid)
            if not skill:
                continue
            rect = pygame.Rect(x0 + i * (size + gap), y0, size, size)
            draw_panel(surface, rect, fill=THEME["skill_bg"],
                       border=THEME["border"], radius=6)
            draw_text(surface, skill["name"][:1], self.f[20],
                      THEME["accent"], rect.center, anchor="center")
            cd = player.skill_cds.get(sid, 0)
            if cd > 0:
                ratio = cd / max(0.01, skill["cooldown"])
                h = int(rect.h * ratio)
                s = pygame.Surface(rect.size, pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                surface.blit(s, rect.topleft,
                             area=pygame.Rect(0, 0, rect.w, h))
                draw_text(surface, f"{cd:.1f}", self.f[15], THEME["text"],
                          rect.center, anchor="center")
            if player.mp < skill["mp_cost"]:
                pygame.draw.rect(surface, (90, 40, 50), rect, width=2,
                                 border_radius=6)
            draw_text(surface, settings.label_for(f"skill_{i + 1}"),
                      self.f[13], THEME["muted"], (rect.x + 3, rect.y + 3),
                      anchor="topleft")

    def _draw_damage_texts(self, surface, combat, cam):
        for t in combat.damage_texts:
            sx, sy = cam.apply_point(t["x"], t["y"])
            size = 22 if t["crit"] else 15
            font = make_font(size, bold=t["crit"])
            draw_text(surface, t["text"], font, t["color"],
                      (int(sx), int(sy)), anchor="center", shadow=True)

    def _draw_boss_bar(self, surface, boss):
        w, h = 520, 20
        x = (surface.get_width() - w) // 2
        y = 64
        draw_panel(surface, pygame.Rect(x - 10, y - 30, w + 20, h + 40),
                   fill=THEME["panel"], border=THEME["border"], radius=10)
        draw_text(surface, boss.name, self.f[20], (255, 220, 120),
                  (surface.get_width() // 2, y - 10), anchor="midbottom",
                  shadow=True)
        ratio = boss.hp / max(1, boss.max_hp)
        ProgressBar((x, y, w, h), ratio, (255, 200, 60)).draw(surface)