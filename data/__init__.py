# -*- coding: utf-8 -*-
"""
data 包 —— 游戏数据层
======================
物品(items) / 技能(skills) / 怪物(monsters) / 地图(maps)
/ NPC(npcs) / 任务(quests)。

所有数据均为“纯字典”，便于对照 wiki 精确微调。
这里统一提供按 id 查询的快捷函数。
"""

from data.items import ITEMS, get_item
from data.skills import SKILLS, get_skill
from data.monsters import MONSTERS, get_monster
from data.maps import MAPS, get_map
from data.npcs import NPCS, get_npc
from data.quests import QUESTS, get_quest

__all__ = [
    "ITEMS", "get_item",
    "SKILLS", "get_skill",
    "MONSTERS", "get_monster",
    "MAPS", "get_map",
    "NPCS", "get_npc",
    "QUESTS", "get_quest",
]