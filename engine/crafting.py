# -*- coding: utf-8 -*-
"""生活系统：采集 (gather)、炼药/烹饪 (cauldron)、锻造 (forge)。

对应 wiki 的采集系统 / 炼药烹饪 / 装备锻造三大生活玩法。
数据全部来自 content JSON；这里只实现通用逻辑。
"""
import random
from .registry import REGISTRY


class GatherSystem:
    def __init__(self, player):
        self.player = player
        # 工具熟练度
        self.tools = {"axe": 0, "pick": 0, "sickle": 0}

    def try_gather(self, gather_id, world, wx, wy):
        """尝试采集某个采集物。返回是否成功、掉落。"""
        g = REGISTRY.get("gather", gather_id)
        if g is None:
            return False
        tool_if = g.get("tool", "axe")
        require_lv = g.get("level", 0)
        if self.tools.get(tool_if, 0) < require_lv:
            return False
        amt = random.randint(g.get("amount", [1, 2])[0], g.get("amount", [1, 2])[-1])
        drop = g.get("drop", "wood_log")
        self.tools[tool_if] += g.get("exp", 2)
        self.player.inventory.add(drop, amt)
        return True, drop, amt

    # ------- 工具装备道具（采集工具本身） -------
    def tool_durability(self):
        """当前手上工具（若有）。"""
        stack = self.player.equipment.get("main_hand")
        if stack and stack.base.get("type") == "tool":
            return stack
        return None


class Cauldron:
    """炼药 / 烹饪锅。重点体现『材料精准与时机』。"""

    def __init__(self, player):
        self.player = player
        self.station = "cauldron"

    def craft(self, recipe_id):
        r = REGISTRY.get("recipe", recipe_id)
        if r is None or r.get("station") != "cauldron":
            return None
        inputs = r.get("inputs")
        if isinstance(inputs, dict):
            for mat, cnt in inputs.items():
                if self.player.inventory.count(mat) < cnt:
                    return None
            for mat, cnt in inputs.items():
                self.player.inventory.remove(mat, cnt)
        result = r.get("result")
        count = r.get("count", 1)
        # 炼药有失败概率（需精准）
        success_rate = r.get("success_rate", 1.0)
        if r.get("kind") == "alchemy" and random.random() > success_rate:
            return "failed"
        self.player.inventory.add(result, count)
        return result


class Forge:
    """铁匠锻造装备。"""

    def __init__(self, player):
        self.player = player

    def craft(self, recipe_id):
        r = REGISTRY.get("recipe", recipe_id)
        if r is None or r.get("station") != "forge":
            return None
        gold = r.get("gold", 0)
        if self.player.inventory.gold < gold:
            return None
        inputs = r.get("inputs")
        if isinstance(inputs, dict):
            for mat, cnt in inputs.items():
                if self.player.inventory.count(mat) < cnt:
                    return None
        self.player.inventory.gold -= gold
        for mat, cnt in inputs.items():
            self.player.inventory.remove(mat, cnt)
        self.player.inventory.add(r.get("result"), r.get("count", 1))
        return r.get("result")
