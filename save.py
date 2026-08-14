# -*- coding: utf-8 -*-
"""
存档系统（save.py）
===================
3 个存档位，JSON 持久化：
  - save_player(slot, player, map_id, pos)
  - load_player(slot) -> (Player, map_id, pos) 或 None
  - info(slot) -> 摘要字典（存档选择界面用）
"""

import json
import os
import time

from config import SAVE_DIR
from entities.player import Player


class SaveManager:
    def __init__(self, slots=3):
        self.slots = slots
        os.makedirs(SAVE_DIR, exist_ok=True)

    def _path(self, slot):
        return os.path.join(SAVE_DIR, f"save_{slot}.json")

    # ------------------------------------------------------------------
    def save_player(self, slot, player, map_id, pos):
        data = {
            "version": 1,
            "class_id": player.class_id,
            "class_name": player.class_name,
            "name": player.name,
            "level": player.level, "exp": player.exp, "gold": player.gold,
            "free_points": player.free_points, "kills": player.kills,
            "stats": player.stats, "hp": player.hp, "mp": player.mp,
            "equipment": player.equipment,
            "inventory": player.inventory,
            "quick_slots": player.quick_slots,
            "skills": player.skills,
            "quests": player.quests,
            "quest_progress": player.quest_progress,
            "map_id": map_id, "pos": list(pos),
            "saved_at": time.strftime("%Y-%m-%d %H:%M"),
        }
        tmp = self._path(slot) + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._path(slot))
        except OSError as exc:
            print(f"[save] 存档失败：{exc}")

    def load_player(self, slot):
        data = self.load(slot)
        if not data:
            return None
        player = Player(data["class_id"], data.get("name", "冒险者"))
        player.level = data["level"]
        player.exp = data["exp"]
        player.gold = data["gold"]
        player.free_points = data["free_points"]
        player.kills = data["kills"]
        player.stats.update(data["stats"])
        player.equipment = dict(data["equipment"])
        player.inventory = list(data["inventory"])
        player.quick_slots = dict(data["quick_slots"])
        player.skills = list(data["skills"])
        player.quests = dict(data["quests"])
        player.quest_progress = {k: list(v)
                                for k, v in data["quest_progress"].items()}
        player.refresh_stats()
        player.hp = data["hp"]
        player.mp = data["mp"]
        return player, data.get("map_id", "town"), tuple(data["pos"])

    # ------------------------------------------------------------------
    def load(self, slot):
        try:
            with open(self._path(slot), "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def info(self, slot):
        """存档摘要（无存档返回 None）。"""
        data = self.load(slot)
        if not data:
            return None
        return {
            "class_name": data.get("class_name", "?"),
            "level": data.get("level", 1),
            "gold": data.get("gold", 0),
            "progress": data.get("map_id", "?"),
            "saved_at": data.get("saved_at", ""),
        }

    def delete(self, slot):
        try:
            os.remove(self._path(slot))
        except OSError:
            pass

    def has_save(self, slot):
        return self.load(slot) is not None