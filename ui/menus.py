# -*- coding: utf-8 -*-
"""
菜单（menus.py）
================
标题 / 选职业 / 选存档 / 暂停 / 设置 / 游戏结束 / 顶部通知。
所有菜单通过回调与游戏层解耦。
"""

import pygame

from config import make_font
from utils import draw_text
from ui.theme import THEME
from ui.widgets import draw_panel, Button, wrap_text


# ======================================================================
class Toast:
    """顶部浮动通知。"""

    def __init__(self):
        self.items = []
        self.font = make_font(16)

    def show(self, text):
        self.items.append({"text": text, "life": 3.0})

    def update(self, dt):
        for t in self.items:
            t["life"] -= dt
        self.items = [t for t in self.items if t["life"] > 0]

    def draw(self, surface):
        y = 20
        for t in self.items:
            w = max(260, self.font.size(t["text"])[0] + 60)
            rect = pygame.Rect((surface.get_width() - w) // 2, y, w, 36)
            draw_panel(surface, rect, fill=(30, 34, 50),
                       border=THEME["accent"], radius=8)
            draw_text(surface, t["text"], self.font, THEME["text"],
                      rect.center, anchor="center")
            y += 46


# ======================================================================
class TitleScreen:
    def __init__(self, on_start, on_settings, on_quit):
        cx = 640
        self.buttons = [
            Button((cx - 140, 380, 280, 54), "开始游戏", on_start),
            Button((cx - 140, 450, 280, 54), "设置", on_settings),
            Button((cx - 140, 520, 280, 54), "退出", on_quit),
        ]
        self.title_font = make_font(60, bold=True)
        self.sub_font = make_font(20)

    def handle_event(self, event):
        for b in self.buttons:
            if b.handle_event(event):
                return True
        return False

    def draw(self, surface):
        surface.fill(THEME["bg"])
        draw_text(surface, "元素之诗：灾厄", self.title_font,
                  THEME["accent"], (640, 220), anchor="center", shadow=True)
        draw_text(surface, "—— 横版动作 RPG ——", self.sub_font,
                  THEME["muted"], (640, 280), anchor="center")
        for b in self.buttons:
            b.draw(surface)


# ======================================================================
class ClassSelect:
    CLASS_INFO = {
        "swordsman": ("魔剑士", "近战物理，剑刃附魔元素", (205, 122, 60)),
        "mage":      ("元素法师", "远程魔法，大范围元素轰击", (80, 140, 255)),
        "archer":    ("风射手", "远程物理，身法灵活多变", (90, 200, 120)),
        "assassin":  ("暗影刺客", "近战高暴击，迅捷致命", (190, 110, 210)),
    }

    def __init__(self, on_choose, on_back):
        self.on_choose = on_choose
        self.on_back = on_back
        self.order = list(self.CLASS_INFO.keys())
        self.selected = 0
        self.font = make_font(18)
        self.title = make_font(34, bold=True)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_back()
                return True
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % 4
            if event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % 4
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                cid = self.order[self.selected]
                self.on_choose(cid)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self.on_choose(self.order[i])
                    return True
        return False

    def _card_rects(self):
        x0, y0 = 140, 260
        w, h = 230, 300
        return [pygame.Rect(x0 + i * (w + 20), y0, w, h) for i in range(4)]

    def draw(self, surface):
        surface.fill(THEME["bg"])
        draw_text(surface, "选择职业", self.title, THEME["accent"],
                  (640, 140), anchor="center")
        for i, cid in enumerate(self.order):
            name, desc, color = self.CLASS_INFO[cid]
            rect = self._card_rects()[i]
            sel = i == self.selected
            draw_panel(surface, rect, fill=THEME["panel_light"] if sel
                       else (30, 34, 46),
                       border=THEME["accent"] if sel else THEME["border"],
                       radius=12)
            # 职业占位形象
            body = pygame.Rect(rect.centerx - 30, rect.y + 40, 60, 90)
            pygame.draw.rect(surface, color, body, border_radius=8)
            pygame.draw.circle(surface, (240, 205, 175),
                               (rect.centerx, rect.y + 28), 20)
            draw_text(surface, name, self.font, THEME["text"],
                      (rect.centerx, rect.y + 160), anchor="center")
            for j, ln in enumerate(wrap_text(desc, self.font, rect.w - 30)):
                draw_text(surface, ln, self.font, THEME["muted"],
                          (rect.centerx, rect.y + 190 + j * 22),
                          anchor="center")
        draw_text(surface, "← → 选择职业 · 回车 确认 · Esc 返回",
                  self.font, THEME["muted"], (640, 620), anchor="center")


# ======================================================================
class SaveSelect:
    def __init__(self, save_manager, on_choose, on_back):
        self.save_manager = save_manager
        self.on_choose = on_choose
        self.on_back = on_back
        self.selected = 0
        self.font = make_font(17)
        self.title = make_font(30, bold=True)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_back()
                return True
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % 3
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % 3
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_choose(self.selected)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._slot_rects()):
                if rect.collidepoint(event.pos):
                    self.on_choose(i)
                    return True
        return False

    def _slot_rects(self):
        return [pygame.Rect(340, 220 + i * 90, 600, 70) for i in range(3)]

    def draw(self, surface):
        surface.fill(THEME["bg"])
        draw_text(surface, "选择存档", self.title, THEME["accent"],
                  (640, 140), anchor="center")
        for i, rect in enumerate(self._slot_rects()):
            info = self.save_manager.info(i)
            sel = i == self.selected
            draw_panel(surface, rect, fill=THEME["panel_light"] if sel
                       else (30, 34, 46),
                       border=THEME["accent"] if sel else THEME["border"],
                       radius=10)
            title = f"存档位 {i + 1}"
            if info:
                title += f"　{info.get('class_name', '?')} · Lv.{info.get('level', 1)}"
            draw_text(surface, title, self.font, THEME["text"],
                      (rect.x + 20, rect.centery), anchor="midleft")
            if info:
                draw_text(surface, f"金币 {info.get('gold', 0)} · 进度 {info.get('progress', '-')}",
                          self.font, THEME["muted"],
                          (rect.right - 20, rect.centery), anchor="midright")
            else:
                draw_text(surface, "新游戏", self.font, THEME["muted"],
                          (rect.right - 20, rect.centery), anchor="midright")
        draw_text(surface, "↑ ↓ 选择 · 回车 确认 · Esc 返回",
                  self.font, THEME["muted"], (640, 560), anchor="center")


# ======================================================================
class PauseMenu:
    def __init__(self, on_resume, on_settings, on_quit):
        cx = 640
        self.buttons = [
            Button((cx - 140, 280, 280, 54), "继续游戏", on_resume),
            Button((cx - 140, 350, 280, 54), "设置", on_settings),
            Button((cx - 140, 420, 280, 54), "保存并退出", on_quit),
        ]
        self.font = make_font(34, bold=True)

    def handle_event(self, event):
        for b in self.buttons:
            if b.handle_event(event):
                return True
        return False

    def draw(self, surface):
        s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        surface.blit(s, (0, 0))
        draw_text(surface, "已暂停", self.font, THEME["accent"],
                  (640, 180), anchor="center")
        for b in self.buttons:
            b.draw(surface)


# ======================================================================
class GameOverScreen:
    def __init__(self, on_respawn, on_quit):
        cx = 640
        self.buttons = [
            Button((cx - 140, 360, 280, 54), "返回主城复活", on_respawn),
            Button((cx - 140, 430, 280, 54), "返回标题", on_quit),
        ]
        self.font = make_font(44, bold=True)

    def handle_event(self, event):
        for b in self.buttons:
            if b.handle_event(event):
                return True
        return False

    def draw(self, surface):
        s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        surface.blit(s, (0, 0))
        draw_text(surface, "你 已 阵 亡", self.font, THEME["danger"],
                  (640, 260), anchor="center", shadow=True)
        for b in self.buttons:
            b.draw(surface)


# ======================================================================
class SettingsMenu:
    def __init__(self, sys, on_back):
        self.sys = sys
        self.on_back = on_back
        self.selected = 0
        self.waiting_key = None        # 正在等待按键的动作
        self.font = make_font(16)
        self.title = make_font(26, bold=True)
        self.items = ["master", "sfx", "music"] + list(sys.DEFAULT_KEYBINDS.keys())
        self.volume_labels = {"master": "总音量", "sfx": "音效音量",
                              "music": "音乐音量"}

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.waiting_key is not None:
                self.sys.remap(self.waiting_key, event.key)
                self.waiting_key = None
                return True
            if event.key == pygame.K_ESCAPE:
                if self.waiting_key:
                    self.waiting_key = None
                else:
                    self.on_back()
                return True
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.items)
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.items)
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self._adjust(event.key == pygame.K_LEFT)
            if event.key == pygame.K_RETURN:
                item = self.items[self.selected]
                if item not in self.volume_labels:
                    self.waiting_key = item
        return False

    def _adjust(self, left):
        item = self.items[self.selected]
        delta = -0.05 if left else 0.05
        if item == "master":
            self.sys.master = max(0.0, min(1.0, self.sys.master + delta))
        elif item == "sfx":
            self.sys.sfx = max(0.0, min(1.0, self.sys.sfx + delta))
        elif item == "music":
            self.sys.music = max(0.0, min(1.0, self.sys.music + delta))
        self.sys.apply_volumes()
        self.sys.save()

    def draw(self, surface):
        draw_panel(surface, (340, 80, 600, 640), fill=THEME["panel"],
                   border=THEME["border"], radius=12)
        draw_text(surface, "设置", self.title, THEME["accent"],
                  (640, 110), anchor="center")
        y = 160
        for i, item in enumerate(self.items):
            rect = pygame.Rect(380, y, 520, 42)
            sel = i == self.selected
            draw_panel(surface, rect, fill=THEME["panel_light"] if sel
                       else (30, 34, 46),
                       border=THEME["accent"] if sel else THEME["border"],
                       radius=6)
            if item in self.volume_labels:
                label = self.volume_labels[item]
                val = getattr(self.sys, item)
                draw_text(surface, label, self.font, THEME["text"],
                          (rect.x + 16, rect.centery), anchor="midleft")
                # 滑条
                bar = pygame.Rect(rect.x + 180, rect.centery - 4, 260, 8)
                pygame.draw.rect(surface, THEME["panel_light"], bar,
                                 border_radius=4)
                pygame.draw.rect(surface, THEME["accent"],
                                 (bar.x, bar.y, int(bar.w * val), bar.h),
                                 border_radius=4)
                draw_text(surface, f"{int(val * 100)}%", self.font,
                          THEME["text"], (rect.right - 16, rect.centery),
                          anchor="midright")
            else:
                label = self.sys.label_for(item)
                key = self.sys.keybinds.get(item)
                draw_text(surface, label, self.font, THEME["text"],
                          (rect.x + 16, rect.centery), anchor="midleft")
                if self.waiting_key == item:
                    draw_text(surface, "按下新按键...", self.font,
                              THEME["accent"], (rect.right - 16, rect.centery),
                              anchor="midright")
                else:
                    draw_text(surface, pygame.key.name(key) if key else "未绑定",
                              self.font, THEME["muted"],
                              (rect.right - 16, rect.centery),
                              anchor="midright")
            y += 50
        draw_text(surface, "↑↓ 选择 · ←→ 音量 · 回车 改键 · Esc 返回",
                  self.font, THEME["muted"], (640, y + 20), anchor="center")