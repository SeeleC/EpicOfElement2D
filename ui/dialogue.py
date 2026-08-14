# -*- coding: utf-8 -*-
"""NPC 对话窗（dialogue.py）"""

import pygame

from config import make_font
from utils import draw_text
from ui.theme import THEME
from ui.widgets import draw_panel, wrap_text, Button


class DialogueBox:
    def __init__(self, sys):
        self.sys = sys
        self.font = make_font(17)
        self.name_font = make_font(20, bold=True)
        self._buttons = []

    # ------------------------------------------------------------------
    def option_rects(self, surface):
        if not self.sys.is_open or not self.sys.prompt:
            return []
        w = min(760, surface.get_width() - 80)
        x = (surface.get_width() - w) // 2
        y = surface.get_height() - 170 - 24
        prompt = self.sys.prompt
        out = []
        if prompt["type"] == "quest_offer":
            out.append((pygame.Rect(x + w - 260, y + 110, 110, 40),
                        "接受", "accept"))
            out.append((pygame.Rect(x + w - 140, y + 110, 110, 40),
                        "拒绝", "decline"))
        elif prompt["type"] == "quest_done":
            out.append((pygame.Rect(x + w - 260, y + 110, 240, 40),
                        "交付任务", "done"))
        return out

    def handle_event(self, event):
        if not self.sys.is_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.sys.close()
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.sys.prompt:
                    if self.sys.prompt["type"] == "quest_offer":
                        self.sys.choose("accept")
                    elif self.sys.prompt["type"] == "quest_done":
                        self.sys.choose("done")
                else:
                    self.sys.advance()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, _label, action in self.option_rects(event.__dict__.get("window", None) or event):
                pass
            for rect, _label, action in self.option_rects(pygame.display.get_surface()):
                if rect.collidepoint(event.pos):
                    self.sys.choose(action)
                    return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.sys.is_open:
            return
        w = min(760, surface.get_width() - 80)
        h = 170
        x = (surface.get_width() - w) // 2
        y = surface.get_height() - h - 24
        draw_panel(surface, (x, y, w, h), fill=THEME["panel"],
                   border=THEME["border"], radius=10)
        npc = self.sys.npc
        draw_text(surface, npc.name, self.name_font, THEME["accent"],
                  (x + 20, y + 14), anchor="topleft")
        ty = y + 48
        for ln in wrap_text(self.sys.current_line(), self.font, w - 40)[:4]:
            draw_text(surface, ln, self.font, THEME["text"],
                      (x + 20, ty), anchor="topleft", shadow=True)
            ty += 26
        for rect, label, action in self.option_rects(surface):
            draw_panel(surface, rect, fill=THEME["panel_light"],
                       border=THEME["accent"], radius=6)
            draw_text(surface, label, self.font, THEME["accent"],
                      rect.center, anchor="center")