# -*- coding: utf-8 -*-
"""掉落在地图上的物品实体（可拾取）。"""
from .entity import Entity
from .inventory import ItemStack
from .vector2 import Vec2


class GroundItem(Entity):
    def __init__(self, item_id, x, y, count=1):
        super().__init__(x, y)
        self.item_id = item_id
        self.count = count
        self.base = self._resolve()
        self.life = 180.0          # 秒后消失

    def _resolve(self):
        from .registry import REGISTRY
        return (REGISTRY.get("item", self.item_id)
                or REGISTRY.get("equipment", self.item_id)
                or REGISTRY.get("trinket", self.item_id) or {})

    @property
    def icon(self):
        return self.base.get("icon", "coin")

    def update(self, dt, world):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def can_pickup(self):
        return self.alive
