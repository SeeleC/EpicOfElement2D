# -*- coding: utf-8 -*-
"""
背包系统（inventory.py）
========================
管理玩家背包：
  - 物品堆叠 / 新格添加 / 移除
  - 使用消耗品（药水等，应用效果后扣数量）
  - 快捷栏（pot_1~4）处理玩家按键使用请求
"""

from data.items import get_item


class InventorySystem:
    MAX_SLOTS = 60

    def __init__(self, player):
        self.player = player
        if not hasattr(player, "inventory"):
            player.inventory = []
        if not hasattr(player, "quick_slots"):
            player.quick_slots = {1: "hp_potion", 2: "mp_potion",
                                  3: "big_hp_potion", 4: None}

    # ------------------------------------------------------------------
    def add(self, item_id, count=1):
        """尝试加入物品，返回实际加入数量（0 表示失败/满）。"""
        item = get_item(item_id)
        if not item:
            return 0
        added = 0
        stack = item["stack"]
        if stack > 1:
            for slot in self.player.inventory:
                if slot["id"] == item_id and slot["count"] < stack:
                    take = min(stack - slot["count"], count - added)
                    slot["count"] += take
                    added += take
                    if added >= count:
                        return added
        while added < count:
            if len(self.player.inventory) >= self.MAX_SLOTS:
                break
            self.player.inventory.append({"id": item_id, "count": 1})
            added += 1
        return added

    def remove(self, item_id, count=1):
        """移除物品，返回是否足够移除。"""
        for i in range(len(self.player.inventory) - 1, -1, -1):
            slot = self.player.inventory[i]
            if slot["id"] != item_id:
                continue
            take = min(slot["count"], count)
            slot["count"] -= take
            count -= take
            if slot["count"] <= 0:
                self.player.inventory.pop(i)
            if count <= 0:
                return True
        return count <= 0

    def count(self, item_id):
        return sum(s["count"] for s in self.player.inventory
                   if s["id"] == item_id)

    # ------------------------------------------------------------------
    def use_at(self, index):
        """使用指定下标背包格（消耗品）。"""
        if not (0 <= index < len(self.player.inventory)):
            return False
        slot = self.player.inventory[index]
        item = get_item(slot["id"])
        if not item or not item["usable"]:
            return False
        if not self.player.use_item(slot["id"]):
            return False
        self.remove(slot["id"], 1)
        return True

    def use_item(self, item_id):
        """按 id 使用一件物品。"""
        item = get_item(item_id)
        if not item or not item["usable"]:
            return False
        if not self.player.use_item(item_id):
            return False
        self.remove(item_id, 1)
        return True

    def process_quick_use(self, player):
        """处理玩家按下的快捷栏使用请求（pot_1..4）。"""
        for i, req in list(player.quick_use.items()):
            if not req:
                continue
            player.quick_use[i] = False
            item_id = player.quick_slots.get(i)
            if item_id:
                self.use_item(item_id)

    # ------------------------------------------------------------------
    def get_consumables(self):
        """返回所有可消耗物品（背包 UI 用）。"""
        out = []
        for i, slot in enumerate(self.player.inventory):
            item = get_item(slot["id"])
            if item and item["usable"]:
                out.append((i, slot, item))
        return out