# -*- coding: utf-8 -*-
"""存档系统。

仿照 Minecraft ：
    - 世界按「区块(Chunk)」持久化：world.to_json() 保存 visited 区块。
    - 玩家数据单独序列化：等级/职业/背包/装备/任务。
    - 存档目录为 saves/<存档名>/：
        save.json         玩家与元数据
        world.json        世界（区块数据）
        quests.json       任务进度（可选）

提供「存档位」选择（3 个存档位）。
"""
import json
import shutil
import time
from pathlib import Path

from . import config


def _json_dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _json_load(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


class SaveManager:
    def __init__(self, save_dir=None):
        self.save_dir = Path(save_dir) if save_dir else config.SAVE_DIR
        self.save_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def list_saves(self):
        """返回每个存档位及其元信息。"""
        result = {}
        for i in range(1, 4):
            slot = self.save_dir / f"slot{i}"
            meta = slot / "meta.json"
            info = _json_load(meta, {})
            result[i] = {
                "exists": slot.exists(),
                "name": info.get("name", f"存档位 {i}"),
                "time": info.get("time", 0),
                "level": info.get("level", 1),
                "klass": info.get("klass", "?"),
            }
        return result

    def save(self, slot, name, game):
        folder = self.save_dir / f"slot{slot}"
        folder.mkdir(parents=True, exist_ok=True)
        world = game.world
        if world.player:
            world.player_pos = [world.player.x, world.player.y]
        _json_dump(folder / "world.json", world.to_json())
        _json_dump(folder / "save.json", game.player_to_json())
        _json_dump(folder / "meta.json", {
            "name": name,
            "time": time.time(),
            "level": game.player.level,
            "klass": game.player.klass,
        })

    def load(self, slot):
        folder = self.save_dir / f"slot{slot}"
        if not (folder / "world.json").exists():
            return None
        world_data = _json_load(folder / "world.json", {})
        player_data = _json_load(folder / "save.json", {})
        meta = _json_load(folder / "meta.json", {})
        return {"world": world_data, "player": player_data, "meta": meta}

    def delete(self, slot):
        folder = self.save_dir / f"slot{slot}"
        if folder.exists():
            shutil.rmtree(folder)
