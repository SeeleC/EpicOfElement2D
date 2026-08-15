# -*- coding: utf-8 -*-
"""HUD：血量 / 资源条 / 等级 / 金币 / 经验条 / 技能栏。"""
from .. import config
from . import draw_util


class HUDBar:
    """一条数值条（血条 / 法力 / 架势）。"""

    def __init__(self, kind="hp"):
        self.kind = kind
        self.width = 240
        self.height = 16
        self._color = config.Palette.HP if kind == "hp" else (
            config.Palette.MP if kind == "mp" else config.Palette.STANCE)

    def draw(self, batch, x, y, cur, max_):
        pct = max(0.0, cur / max_) if max_ else 0.0
        draw_util.add_rect(batch, x, y, self.width, self.height, config.Palette.DARK)
        w = int(self.width * min(1.0, pct))
        draw_util.add_rect(batch, x, y, w, self.height, self._color)
        draw_util.add_border(batch, x, y, self.width, self.height, (0, 0, 0, 180))
        draw_util.add_text(batch, f"{int(cur)}/{int(max_)}",
                           x + self.width / 2, y + self.height / 2,
                           size=10, anchor_x="center", anchor_y="center",
                           color=(255, 255, 255))


class HUD:
    def __init__(self, game):
        self.game = game
        self.hp = HUDBar("hp")
        self.mp = HUDBar("mp")

    def draw(self, batch):
        p = self.game.player
        if p is None:
            return
        m = 12
        self.hp.draw(batch, m, m, p.hp, p.max_hp)
        self.mp.draw(batch, m, m + 22, p.resource, p.max_resource)

        draw_util.add_text(batch, f"Lv.{p.level} · {p.klass_name()}",
                           m + self.hp.width + 12, m + 8,
                           size=14, anchor_x="left", color=(255, 255, 255))

        draw_util.add_text(batch, f"金币: {p.inventory.gold}",
                           self.game.width - m, m + 8,
                           size=14, anchor_x="right", color=config.Palette.GOLD)

        # 经验条
        xp_x, xp_y = m, m + 44
        pw = self.hp.width
        exp_cur = p.exp
        exp_need = p.exp_to_next()
        draw_util.add_rect(batch, xp_x, xp_y, pw, 8, config.Palette.DARK)
        w = int(pw * min(1.0, exp_cur / exp_need if exp_need else 0))
        draw_util.add_rect(batch, xp_x, xp_y, w, 8, (120, 200, 255))
        draw_util.add_text(batch, f"EXP {exp_cur}/{exp_need}",
                           xp_x + pw / 2, xp_y + 4, size=8,
                           anchor_x="center", anchor_y="center", color=(0, 0, 0))

        self._draw_skillbar(batch)
        self._draw_equip_hint(batch)

    def _draw_skillbar(self, batch):
        p = self.game.player
        if not p or not p.skills_learned:
            return
        slots = 5
        sw = 36
        start_x = 20
        y = self.game.height - 30
        for i in range(slots):
            x = start_x + i * (sw + 4)
            draw_util.add_rect(batch, x, y, sw, sw, (40, 40, 50, 200))
            draw_util.add_border(batch, x, y, sw, sw, (0, 0, 0, 220))
            if i < len(p.skills_learned):
                skill_id = p.skills_learned[i]
                name = p.skill_name(skill_id)
                draw_util.add_text(batch, str(i + 1) if len(name) > 4 else name,
                                   x + sw / 2, y + sw / 2, size=9,
                                   color=(230, 230, 230),
                                   anchor_x="center", anchor_y="center")
            else:
                draw_util.add_text(batch, str(i + 1), x + sw / 2, y + sw / 2,
                                   size=10, color=(90, 90, 100),
                                   anchor_x="center", anchor_y="center")

    def _draw_equip_hint(self, batch):
        p = self.game.player
        if not p:
            return
        w = self.game.width
        main = p.equipment.get("main_hand")
        if main:
            draw_util.add_text(batch, "武器: " + (main.base.get("name") or main.item_id),
                               w - 20, self.game.height - 30, size=12,
                               anchor_x="right", color=(230, 230, 230))
