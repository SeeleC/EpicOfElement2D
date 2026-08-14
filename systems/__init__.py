# -*- coding: utf-8 -*-
"""
systems 包 —— 系统层
=====================
战斗(combat) / 背包(inventory) / 装备(equipment) / 升级加点(level_up)
/ 任务(quest) / 对话(dialogue) / 商店(shop) / 设置(settings)。

系统层负责“规则与结算”，通过持有 player / scene / game 引用来工作。
"""

from systems.combat import CombatSystem
from systems.inventory import InventorySystem
from systems.equipment import EquipmentSystem
from systems.level_up import LevelUpSystem, ALLOC_STATS, STAT_LABELS
from systems.quest import QuestSystem
from systems.dialogue import DialogueSystem
from systems.shop import ShopSystem
from systems.settings import SettingsSystem

__all__ = [
    "CombatSystem", "InventorySystem", "EquipmentSystem", "LevelUpSystem",
    "ALLOC_STATS", "STAT_LABELS", "QuestSystem", "DialogueSystem",
    "ShopSystem", "SettingsSystem",
]