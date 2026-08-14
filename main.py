# -*- coding: utf-8 -*-
"""
《元素之诗：灾厄》 —— 主程序入口
================================
运行：python main.py
依赖：pygame（见 requirements.txt）
"""

import pygame

from config import WINDOW, make_font
from entities.player import Player
from systems.combat import CombatSystem
from systems.dialogue import DialogueSystem
from systems.equipment import EquipmentSystem
from systems.inventory import InventorySystem
from systems.level_up import LevelUpSystem
from systems.quest import QuestSystem
from systems.settings import SettingsSystem
from systems.shop import ShopSystem
from ui.character import CharacterPanel  # noqa: F401
from ui.hud import HUD
from ui.menus import (TitleScreen, ClassSelect, SaveSelect, PauseMenu,
                      GameOverScreen, SettingsMenu, Toast)
from ui.theme import THEME
from ui.widgets import Button, draw_panel
from utils import draw_text
from save import SaveManager
from sound import SoundManager
from scene import Scene


def _safe_imports():
    missing = []
    for name in ("pygame", "config", "utils", "data", "entities",
                 "systems", "ui", "save", "sound", "scene", "particles"):
        try:
            __import__(name)
        except Exception as exc:
            missing.append(f"{name}: {exc}")
    if missing:
        print("[启动] 以下模块缺失：")
        for m in missing:
            print("  ", m)
    return missing


# ======================================================================
class VictoryScreen:
    def __init__(self, on_continue, on_quit):
        cx = 640
        self.buttons = [
            Button((cx - 140, 380, 280, 54), "返回主城", on_continue),
            Button((cx - 140, 450, 280, 54), "返回标题", on_quit),
        ]
        self.font = make_font(44, bold=True)

    def handle_event(self, event):
        for b in self.buttons:
            if b.handle_event(event):
                return True
        return False

    def draw(self, surface):
        draw_text(surface, "灾厄已被平定！", self.font, THEME["accent"],
                  (640, 260), anchor="center", shadow=True)
        for b in self.buttons:
            b.draw(surface)


# ======================================================================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(WINDOW)
        pygame.display.set_caption("元素之诗：灾厄")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "title"       # title/class_select/save_select/playing/pause/settings/game_over/victory
        self._settings_from = None

        # 基础服务
        self.settings = SettingsSystem(None)
        self.sound = SoundManager()
        self.settings.sound = self.sound
        self.settings.apply_volumes()
        self.toast = Toast()
        self.save_mgr = SaveManager()

        # 字体
        self.font_banner = make_font(46, bold=True)

        # 玩家与系统
        self.player = None
        self.scene = None
        self.hud = HUD()
        self.combat = CombatSystem()
        self.inv = None
        self.equip = None
        self.quest = None
        self.level_up = LevelUpSystem()
        self.dialogue = DialogueSystem(self)
        self.shop = None

        # 菜单
        self._build_menus()

    # ------------------------------------------------------------------
    def _build_menus(self):
        self.title = TitleScreen(self._to_class_select,
                                 lambda: self._to_settings("title"),
                                 self.quit)
        self.class_sel = ClassSelect(self._to_save_select, self._to_title)
        self.save_sel = SaveSelect(self.save_mgr, self._choose_slot,
                                   self._to_class_select)
        self.pause = PauseMenu(self._resume,
                               lambda: self._to_settings("pause"),
                               self._save_and_quit)
        self.game_over = GameOverScreen(self._respawn, self._to_title)
        self.victory = VictoryScreen(self._continue_after_win, self._to_title)
        self.settings_menu = SettingsMenu(self.settings,
                                          self._back_from_settings)

    # ==================================================================
    # 状态切换
    # ==================================================================
    def _to_title(self):
        self.state = "title"

    def _to_class_select(self):
        self.state = "class_select"

    def _to_save_select(self, class_id):
        self._pending_class = class_id
        self.state = "save_select"

    def _choose_slot(self, slot):
        self._slot = slot
        loaded = self.save_mgr.load_player(slot)
        if loaded:
            player, map_id, pos = loaded
            self._init_systems(player)
            self.load_stage(map_id, spawn=pos)
        else:
            player = Player(self._pending_class, "冒险者")
            self._init_systems(player)
            self.quest.start("main_1")       # 新手引导主线
            self.load_stage("town")
        self.state = "playing"
        self.toast.show(f"欢迎回来，{player.class_name} Lv.{player.level}")

    def _resume(self):
        self.state = "playing"

    def _to_settings(self, src):
        self._settings_from = src
        self.state = "settings"

    def _back_from_settings(self):
        self.state = self._settings_from or "title"

    def _save_and_quit(self):
        self._save_game()
        self.state = "title"

    def _save_game(self):
        if self.player and self.scene:
            self.save_mgr.save_player(self._slot, self.player,
                                      self.scene.stage_id,
                                      (self.player.rect.x, self.player.rect.y))
            self.toast.show("已保存")

    def _respawn(self):
        self.player.hp = self.player.max_hp
        self.player.mp = self.player.max_mp
        self.player.state = "idle"
        self.load_stage("town")
        self.state = "playing"
        self.toast.show("你已在主城复活")

    def _continue_after_win(self):
        self.load_stage("town")
        self.state = "playing"

    def win(self):
        self.state = "victory"
        self.toast.show("主线完成！")

    def quit(self):
        self.running = False

    # ==================================================================
    # 玩家与系统
    # ==================================================================
    def _init_systems(self, player):
        self.player = player
        self.combat = CombatSystem()
        self.inv = InventorySystem(player)
        self.equip = EquipmentSystem(player, self.inv)
        self.quest = QuestSystem(player, self)
        self.shop = ShopSystem(player, self.inv)
        self.dialogue = DialogueSystem(self)
        self.equip.refresh()
        self.player.return_town_requested = False

    def load_stage(self, stage_id, spawn=None):
        systems = {"combat": self.combat, "inv": self.inv,
                   "equip": self.equip, "level": self.level_up,
                   "quest": self.quest}
        self.scene = Scene(self, stage_id, self.player, systems, spawn=spawn)

    def change_stage(self, stage_id):
        self._save_game()
        self.load_stage(stage_id)

    # ==================================================================
    # 主循环
    # ==================================================================
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()
            # ★ 新增：处理窗口关闭（点右上角 X）
            for event in events:
                if event.type == pygame.QUIT:
                    if self.player is not None and self.state in ("playing", "pause"):
                        self._save_game()  # 顺手存档
                    self.quit()  # running = False，退出主循环
            pressed_keys = {e.key for e in events if e.type == pygame.KEYDOWN}
            keys_down = pygame.key.get_pressed()
            esc = pygame.K_ESCAPE in pressed_keys

            if self.state == "title":
                for e in events:
                    self.title.handle_event(e)
                self.title.draw(self.screen)

            elif self.state == "class_select":
                for e in events:
                    self.class_sel.handle_event(e)
                self.class_sel.draw(self.screen)

            elif self.state == "save_select":
                for e in events:
                    self.save_sel.handle_event(e)
                self.save_sel.draw(self.screen)

            elif self.state == "playing":
                self._run_playing(dt, events, pressed_keys, keys_down, esc)

            elif self.state == "pause":
                for e in events:
                    self.pause.handle_event(e)
                self.scene.draw(self.screen)
                self.pause.draw(self.screen)

            elif self.state == "settings":
                for e in events:
                    self.settings_menu.handle_event(e)
                if self.state in ("playing", "pause"):
                    self.scene.draw(self.screen)
                else:
                    self.screen.fill(THEME["bg"])
                self.settings_menu.draw(self.screen)

            elif self.state == "game_over":
                for e in events:
                    self.game_over.handle_event(e)
                self.scene.draw(self.screen)
                self.game_over.draw(self.screen)

            elif self.state == "victory":
                for e in events:
                    self.victory.handle_event(e)
                self.screen.fill((18, 16, 28))
                self.victory.draw(self.screen)

            self.toast.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

    def _run_playing(self, dt, events, pressed_keys, keys_down, esc):
        held, pressed = self.settings.build_actions(keys_down, pressed_keys)
        consumed = self.scene.handle_event(events, pressed)
        if self.scene.overlay is None:
            if esc and not consumed:
                self.state = "pause"
                self._save_game()
                return
            self.scene.handle_input(held, pressed)
        self.scene.update(dt)
        self.scene.draw(self.screen)

        # HUD
        self.player._hud_boss = self.scene.active_boss
        self.hud.draw(self.screen, self.player, self.combat,
                      self.settings, self.scene.cam)

        if self.scene.dead:
            self.game_over  # noqa
            self.state = "game_over"
            self.sound.play("death")


# ======================================================================
if __name__ == "__main__":
    _safe_imports()
    Game().run()