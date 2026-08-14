# -*- coding: utf-8 -*-
"""
存档系统（save.py）
===================
负责玩家数据的 新建 / 读取 / 保存 / 删除：
  - 以 slot_N.json 形式存于 data/saves/；
  - 写入采用“临时文件 + 原子改名”，避免写一半损坏存档；
  - new_player_data() 按职业生成初始角色（属性来自 config.CLASSES）。

后续 背包/装备/技能树/任务 模块就绪后，会往 data 里填入对应字段，
存档结构已经为此预留了位置。
"""

import json
import os

from config import CLASSES, START_LEVEL, MAX_LEVEL, SAVE_DIR


class SaveManager:
    def __init__(self, save_dir=None):
        self.save_dir = save_dir or SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 存档路径
    # ------------------------------------------------------------------
    def _path(self, slot):
        return os.path.join(self.save_dir, f"slot_{int(slot)}.json")

    @staticmethod
    def _slot_of(filename):
        """由文件名反推槽位号：slot_3.json -> 3。"""
        try:
            return int(filename.replace("slot_", "").replace(".json", ""))
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # 新建角色
    # ------------------------------------------------------------------
    def new_player_data(self, class_id, name="冒险者"):
        """按职业模板创建初始角色数据字典。"""
        cls = CLASSES.get(class_id)
        if cls is None:
            raise ValueError(f"未知职业：{class_id}")
        base = cls["base"]
        return {
            "version": 1,
            "name": name,
            "class_id": class_id,
            "class_name": cls["name"],
            "level": START_LEVEL,
            "exp": 0,
            "gold": 500,                       # 初始金币
            # 当前属性（由 base + 装备 + 加点共同决定）
            "stats": {
                "hp": base["hp"], "mp": base["mp"],
                "atk": base["atk"], "defense": base["defense"],
                "crit": base["crit"], "crit_dmg": base["crit_dmg"],
                "move_speed": base["move_speed"],
            },
            "hp": base["hp"], "mp": base["mp"],   # 当前生命 / 魔法
            "free_points": 0,                  # 升级可分配属性点
            "inventory": [],                   # 背包（items 模块就绪后使用）
            "equipment": {},                   # 装备栏（equipment 模块使用）
            "skills": list(cls["skills"]),     # 已习得技能
            "skill_hotbar": [],                # 技能快捷栏
            "quests": {},                      # 任务进度（quest 模块使用）
            "scene": "town",                   # 当前所在场景
            "position": [400, 300],            # 出生点
            "play_time": 0.0,
            "kills": 0,
        }

    # ------------------------------------------------------------------
    # 读写
    # ------------------------------------------------------------------
    def save(self, slot, data):
        """把 data 保存到槽位 slot。使用原子写入防损坏。"""
        path = self._path(slot)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)   # 原子替换
            return True
        except OSError as exc:
            print(f"[save] 写入槽位 {slot} 失败：{exc}")
            return False

    def load(self, slot):
        """读取槽位存档；不存在或损坏返回 None。"""
        path = self._path(slot)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except (OSError, ValueError):
            return None

    def delete(self, slot):
        try:
            os.remove(self._path(slot))
            return True
        except OSError:
            return False

    def has_save(self, slot):
        return os.path.exists(self._path(slot))

    # ------------------------------------------------------------------
    def list_slots(self):
        """返回所有已存在存档的槽位号（升序）。"""
        slots = []
        for fn in os.listdir(self.save_dir):
            if fn.startswith("slot_") and fn.endswith(".json"):
                s = self._slot_of(fn)
                if s is not None:
                    slots.append(s)
        return sorted(slots)


# 全局共享存档管理器
save_manager = SaveManager()


if __name__ == "__main__":
    # 自检：建号 -> 保存 -> 读取
    mgr = SaveManager(save_dir=SAVE_DIR)
    p = mgr.new_player_data("swordsman", "测试冒险者")
    print("新建角色：", p["name"], "/", p["class_name"],
          "Lv.", p["level"], "HP", p["hp"])
    mgr.save(99, p)
    loaded = mgr.load(99)
    print("读回存档：", loaded["name"], "/", loaded["class_name"])
    print("槽位列表：", mgr.list_slots())
    mgr.delete(99)
    print("删除后  :", mgr.list_slots())