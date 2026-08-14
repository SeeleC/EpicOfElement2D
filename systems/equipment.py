# -*- coding: utf-8 -*-
"""
装备系统（equipment.py）
========================
六格装备栏：武器 / 头盔 / 胸甲 / 靴子 / 项链 / 戒指。
装备 / 卸下 / 自动汇总属性到 player.equip_bonus 并刷新面板。
"""

from data.items import get_item

SLOT_ORDER = ["weapon", "helmet", "armor", "boots", "necklace", "ring"]
SLOT_LABELS = {
    "weapon": "武器", "helmet": "头盔", "armor": "胸甲",
    "boots": "靴子", "necklace": "项链", "ring": "戒指",
}


class EquipmentSystem:
    def __init__(self, player, inventory=None):
        self.player = player
        self.inventory = inventory
        if not hasattr(player, "equipment"):
            player.equipment = {}

    # ------------------------------------------------------------------
    def equip(self, item_id):
        """从背包装备一件物品；旧装备自动放回背包。"""
        item = get_item(item_id)
        if not item or item.get("slot") not in SLOT_ORDER:
            return False
        if self.inventory is None or self.inventory.count(item_id) <= 0:
            return False
        slot = item["slot"]
        old = self.player.equipment.get(slot)
        if old:
            self.inventory.add(old, 1)
        self.player.equipment[slot] = item_id
        self.inventory.remove(item_id, 1)
        self.refresh()
        return True

    def unequip(self, slot):
        """卸下某槽装备（若背包有空间）。"""
        if slot not in SLOT_ORDER:
            return False
        item_id = self.player.equipment.pop(slot, None)
        if item_id and self.inventory is not None:
            self.inventory.add(item_id, 1)
        self.refresh()
        return True

    # ------------------------------------------------------------------
    def compute_bonus(self):
        """汇总所有已装备物品的属性加成。"""
        bonus = {}
        for slot, item_id in self.player.equipment.items():
            item = get_item(item_id)
            if not item:
                continue
            for k, v in (item.get("stats") or {}).items():
                bonus[k] = bonus.get(k, 0.0) + v
        return bonus

    def refresh(self):
        self.player.equip_bonus = self.compute_bonus()
        self.player.refresh_stats()

    # ------------------------------------------------------------------
    def slot_item(self, slot):
        """返回某槽位的物品字典（无则 None）。"""
        item_id = self.player.equipment.get(slot)
        return get_item(item_id) if item_id else None

    def total_power(self):
        """粗略战力：攻击 + 防御*0.5 + 生命*0.05。"""
        s = self.player
        return (s.get_stat("atk") + s.get_stat("defense") * 0.5
                + s.get_stat("hp") * 0.05)