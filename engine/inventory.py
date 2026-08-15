# -*- coding: utf-8 -*-
"""背包 / 物品栈系统。

ItemStack 表示「某个物品定义的若干数量实例」。
背包按格子存放物品栈，支持堆叠与排序。
"""
from .registry import REGISTRY


class ItemStack:
    """一个可堆叠的物品实例。"""

    def __init__(self, item_id, count=1):
        self.base = REGISTRY.get("item", item_id) \
            or REGISTRY.get("equipment", item_id) \
            or REGISTRY.get("trinket", item_id)
        # 若不在通用分类，再查 equipment/trinket 已由上面覆盖
        if self.base is None:
            self.base = {}
        self.item_id = item_id
        self.count = int(count)

    # ------ 属性代理 ------
    @property
    def name(self):
        return self.base.get("name", self.item_id)

    @property
    def quality(self):
        return self.base.get("quality", "common")

    @property
    def type(self):
        return self.base.get("type", "misc")

    @property
    def is_equipment(self):
        return "slot" in self.base

    @property
    def split_category(self):
        """内容分类，用于装备/材料/消耗品分流。"""
        return self.base.content_type if self.base else "misc"

    @property
    def stackable(self):
        return self.base.get("stack", 1) if self.base else 1

    def max_stack(self):
        return self.base.get("stack", 1)

    def can_stack_with(self, other):
        if other is None:
            return False
        return other.item_id == self.item_id

    def add_count(self, n):
        """尝试堆叠，返回未能放入的剩余数量。"""
        cap = self.max_stack()
        space = cap - self.count
        add = min(space, n)
        self.count += add
        return n - add

    def to_json(self):
        return {"id": self.item_id, "count": self.count}

    @classmethod
    def from_json(cls, data):
        return cls(data["id"], data.get("count", 1))

    def __repr__(self):
        return f"<ItemStack {self.item_id} x{self.count}>"


class Inventory:
    """格子背包。"""

    def __init__(self, size=36):
        self.size = size
        self.slots = [None] * size
        self.gold = 0

    def add(self, item_id, count=1):
        """返回成功添加的数量。"""
        if count <= 0:
            return 0
        added = 0
        # 先尝试堆叠到已有栈
        for i, stack in enumerate(self.slots):
            if stack and stack.item_id == item_id:
                cur_add = stack.add_count(count)
                added += (count - cur_add)
                count = cur_add
                if count <= 0:
                    return count + added - cur_add or added
        # 再有空位新建栈
        while count > 0:
            stack = ItemStack(item_id, min(count, 64))
            count -= stack.count
            empty = self.first_empty()
            if empty is None:
                self.gold += self.discard_value(item_id) * stack.count
                break
            self.slots[empty] = stack
            added += stack.count
        return added

    def first_empty(self):
        for i, s in enumerate(self.slots):
            if s is None:
                return i
        return None

    def count(self, item_id):
        return sum(s.count for s in self.slots if s and s.item_id == item_id)

    def remove(self, item_id, count):
        rem = count
        for i, s in enumerate(self.slots):
            if s and s.item_id == item_id:
                take = min(s.count, rem)
                s.count -= take
                rem -= take
                if s.count <= 0:
                    self.slots[i] = None
                if rem <= 0:
                    return True
        return rem <= 0

    def equipment_instances(self):
        """遍历装备类物品栈。"""
        for s in self.slots:
            if s and s.is_equipment:
                yield s

    def discard_value(self, item_id):
        base = REGISTRY.get("item", item_id)
        return base.get("price", 0) if base else 0

    def to_json(self):
        return {
            "gold": self.gold,
            "slots": [None if s is None else s.to_json() for s in self.slots],
        }

    @classmethod
    def from_json(cls, data):
        inv = cls(len(data.get("slots", [])))
        inv.gold = data.get("gold", 0)
        for i, sd in enumerate(data.get("slots", [])):
            if sd is not None:
                inv.slots[i] = ItemStack.from_json(sd)
        return inv
