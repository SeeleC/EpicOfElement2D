# -*- coding: utf-8 -*-
"""任务面板（quest.py）：当前进行中的任务与目标进度。"""

from config import make_font
from utils import draw_text
from data.quests import get_quest
from ui.theme import THEME
from ui.widgets import draw_panel, ProgressBar


class QuestPanel:
    def __init__(self, sys):
        self.sys = sys
        self.font = make_font(15)
        self.title = make_font(20, bold=True)

    def draw(self, surface):
        draw_panel(surface, (560, 120, 400, 440), fill=THEME["panel"],
                   border=THEME["border"], radius=12)
        draw_text(surface, "任务", self.title, THEME["accent"],
                  (600, 140), anchor="topleft")
        active = self.sys.active_quests()
        if not active:
            draw_text(surface, "当前没有进行中的任务。", self.font,
                      THEME["muted"], (600, 190), anchor="topleft")
            return
        y = 190
        for q in active[:4]:
            qid = q["id"]
            prog = self.sys.player.quest_progress.get(qid, [])
            name_col = THEME["accent"] if q["type"] == "main" else THEME["text"]
            draw_text(surface, f"{'【主线】' if q['type'] == 'main' else '【支线】'}{q['name']}",
                      self.font, name_col, (600, y), anchor="topleft")
            y += 22
            for i, obj in enumerate(q["objectives"]):
                cur = prog[i] if i < len(prog) else 0
                need = obj.get("count", 1)
                done = cur >= need
                col = THEME["ok"] if done else THEME["muted"]
                draw_text(surface, f"{'✔' if done else '·'} {obj['text']}"
                                  f" ({cur}/{need})", self.font, col,
                          (620, y), anchor="topleft")
                y += 20
            # 进度条
            total = sum(min(prog[i], o.get("count", 1))
                        for i, o in enumerate(q["objectives"]))
            need_total = sum(o.get("count", 1) for o in q["objectives"])
            ratio = total / max(1, need_total)
            ProgressBar((600, y, 320, 6), ratio, THEME["exp"]).draw(surface)
            y += 26