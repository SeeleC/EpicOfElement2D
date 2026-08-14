# -*- coding: utf-8 -*-
"""
设置系统（settings.py）
=======================
  - 键位绑定（动作 -> pygame 键码），可重映射并持久化到 settings.json
  - 音量设置（主 / 音效 / 音乐）
  - 把键盘状态转换为玩家可消费的 (held, pressed) 动作集合
"""

import json
import os

import pygame

from config import SAVE_DIR, make_font  # noqa: F401


class SettingsSystem:
    DEFAULT_KEYBINDS = {
        "move_left": pygame.K_a,
        "move_right": pygame.K_d,
        "jump": pygame.K_SPACE,
        "crouch": pygame.K_s,
        "dodge": pygame.K_k,
        "attack": pygame.K_j,
        "skill_1": pygame.K_u,
        "skill_2": pygame.K_i,
        "skill_3": pygame.K_o,
        "skill_4": pygame.K_p,
        "skill_5": pygame.K_l,
        "skill_6": pygame.K_SEMICOLON,
        "interact": pygame.K_e,
        "inventory": pygame.K_b,
        "pot_1": pygame.K_1,
        "pot_2": pygame.K_2,
        "pot_3": pygame.K_3,
        "pot_4": pygame.K_4,
    }
    KEY_NAMES = {  # 设置 UI 显示用
        "move_left": "向左移动", "move_right": "向右移动", "jump": "跳跃",
        "crouch": "下蹲", "dodge": "闪避", "attack": "攻击",
        "skill_1": "技能1", "skill_2": "技能2", "skill_3": "技能3",
        "skill_4": "技能4", "skill_5": "技能5", "skill_6": "技能6",
        "interact": "交互", "inventory": "背包",
        "pot_1": "快捷栏1", "pot_2": "快捷栏2",
        "pot_3": "快捷栏3", "pot_4": "快捷栏4",
    }

    def __init__(self, sound_manager=None):
        self.keybinds = dict(self.DEFAULT_KEYBINDS)
        self.sound = sound_manager
        self.master = 0.8
        self.sfx = 1.0
        self.music = 0.6
        self.path = os.path.join(SAVE_DIR, "settings.json")
        self.load()

    # ------------------------------------------------------------------
    # 键位
    # ------------------------------------------------------------------
    def action_for_key(self, key):
        for action, k in self.keybinds.items():
            if k == key:
                return action
        return None

    def label_for(self, action):
        return self.KEY_NAMES.get(action, action)

    def remap(self, action, key):
        """重映射某动作到新键。"""
        if action not in self.keybinds:
            return False
        for a, k in self.keybinds.items():   # 避免键位冲突（清旧绑定）
            if k == key:
                self.keybinds[a] = None
        self.keybinds[action] = key
        self.save()
        return True

    def build_actions(self, keys_down, key_down_events):
        """keys_down: 当前按住的键集合；key_down_events: 本帧新按下的键集合。
        返回 (held动作集合, pressed动作集合)。"""
        held, pressed = set(), set()
        for action, key in self.keybinds.items():
            if key is None:
                continue
            if key in keys_down:
                held.add(action)
            if key in key_down_events:
                pressed.add(action)
        return held, pressed

    # ------------------------------------------------------------------
    # 音量
    # ------------------------------------------------------------------
    def apply_volumes(self):
        if self.sound:
            self.sound.set_master(self.master)
            self.sound.set_sfx_volume(self.sfx)
            self.sound.set_music_volume(self.music)

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.keybinds.update({k: v for k, v in data.get("keybinds", {}).items()})
            self.master = float(data.get("master", self.master))
            self.sfx = float(data.get("sfx", self.sfx))
            self.music = float(data.get("music", self.music))
        except (OSError, ValueError):
            pass
        self.apply_volumes()

    def save(self):
        data = {
            "keybinds": self.keybinds,
            "master": self.master, "sfx": self.sfx, "music": self.music,
        }
        os.makedirs(SAVE_DIR, exist_ok=True)
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except OSError as exc:
            print(f"[settings] 保存失败：{exc}")