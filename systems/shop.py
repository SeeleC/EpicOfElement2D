# -*- coding: utf-8 -*-
"""
商店系统（shop.py）
===================
买卖规则：买价 = price * 2，卖价 = price。
按 NPC 的 shop 配置（分类 -> 物品id）展示可售商品。
"""

from data.items import get_item


class ShopSystem:
    def __init__(self, player, inventory=None):
        self.player = player
        self.inventory = inventory
        self.npc = None

    # ------------------------------------------------------------------
    @property
    def is_open(self):
        return self.npc is not None

    def open(self, npc):
        self.npc = npc

    def close(self):
        self.npc = None

    # ------------------------------------------------------------------
    @staticmethod
    def buy_price(item):
        return item["price"] * 2

    @staticmethod
    def sell_price(item):
        return item["price"]

    def listing(self):
        """返回 [(物品, 买价), ...]"""
        out = []
        if not self.npc:
            return out
        for cat, ids in (self.npc.shop or {}).items():
            for iid in ids:
                item = get_item(iid)
                if item:
                    out.append((item, self.buy_price(item)))
        return out

    # ------------------------------------------------------------------
    def buy(self, item_id, count=1):
        item = get_item(item_id)
        if not item:
            return False, "未知物品"
        cost = self.buy_price(item) * count
        if self.player.gold < cost:
            return False, "金币不足"
        if self.inventory is not None:
            got = self.inventory.add(item_id, count)
            if got < count:
                return False, "背包空间不足"
        self.player.gold -= cost
        return True, ""

    def sell(self, index, count=1):
        """出售背包第 index 格物品。"""
        if self.inventory is None:
            return False
        slots = self.inventory.player.inventory
        if not (0 <= index < len(slots)):
            return False
        slot = slots[index]
        item = get_item(slot["id"])
        if not item:
            return False
        n = min(slot["count"], count)
        gain = self.sell_price(item) * n
        self.inventory.remove(slot["id"], n)
        self.player.gold += gain
        return True