# -*- coding: utf-8 -*-
"""NPC 实体：对话、商店、炼药锅、铁匠等交互节点。

NPC 的定义来自 npc.json。它的行为（对话文本、售卖、服务）由
engine 的通用服务系统解释，从而可任意扩展新 NPC。
"""
from .entity import Entity
from .registry import REGISTRY


class NPC(Entity):
    def __init__(self, npc_id, x=0.0, y=0.0):
        super().__init__(x, y)
        self.npc_id = npc_id
        self.base = REGISTRY.get("npc", npc_id) or {}
        self.interactable = True
        self.interact_range = 2.0
        self.parent_obj = self
        self.role = self.base.get("role", "merchant")
        self.sells = self.base.get("sells", [])
        self.dialog = self.base.get("dialog", {})
        self.quests = self.base.get("quests", [])

    @property
    def name(self):
        return self.base.get("name", self.npc_id)

    def greet(self):
        return self.dialog.get("greet", "...")

    def serve(self, kind):
        return self.role == kind
