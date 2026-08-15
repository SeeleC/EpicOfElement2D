# -*- coding: utf-8 -*-
"""玩家实体：职业属性、装备、等级经验、资源、技能与交互。"""
from .entity import Entity
from .inventory import Inventory, ItemStack
from .registry import REGISTRY


class Player(Entity):
    def __init__(self, x=8.0, y=8.0):
        super().__init__(x, y)
        self.level = 1
        self.exp = 0
        self.klass = "swordsman"        # 当前职业 id
        self.klass_data = {}

        self.inventory = Inventory(24)
        self.skills_learned = []        # 已学习技能 id（与职业相关）
        self.quests = {}                # quest_id -> 进度状态
        self.equipment = {              # 装备槽位
            "head": None, "body": None, "main_hand": None,
            "off_hand": None, "trinket": None,
        }
        self.attack_state = "idle"      # 攻击动画状态
        self.dash_cd = 0.0
        self.blocking = False           # 剑士招架

        self.auto_level_base_stats()
        self.recalc_stats()
        self.auto_learn_skills()

    # ------------------------------------------------------------------
    def auto_level_base_stats(self):
        klass = REGISTRY.get("class", self.klass)
        self.klass_data = klass or {}
        base = klass.get("base_stats", {}) if klass else {}
        self.max_hp = base.get("hp", 120)
        self.hp = self.max_hp
        self.max_resource = base.get("mana", 100) or base.get("stance", 100)
        self.resource = self.max_resource
        self.speed = base.get("move_speed", 3.0)
        self._base_attack = base.get("attack", 10)
        self._base_magic = base.get("magic", 0)
        self._base_def = base.get("defense", 3)
        self._crit_rate = base.get("crit_rate", 0.05)
        self._crit_damage = base.get("crit_damage", 1.5)

    def recalc_stats(self):
        """综合职业基础 + 等级成长 + 装备加成。"""
        klass = self.klass_data or {}
        per = klass.get("per_level", {})
        lv = self.level - 1
        self.max_hp = (self.klass_data.get("base_stats", {}).get("hp", 120)
                       + per.get("hp", 20) * lv)
        self._atk = (self._base_attack + per.get("attack", 0) * lv)
        self._magic = (self._base_magic + per.get("magic", 0) * lv)
        self._def = self._base_def + per.get("defense", 0) * lv
        self.resource = self.max_resource
        # 装备加成
        for slot, stack in self.equipment.items():
            if stack is None:
                continue
            stats = stack.base.get("stats", {})
            self.max_hp += stats.get("hp", 0)
            if stats.get("hp") and self.hp > 0:
                self.hp += stats.get("hp", 0)
            self._atk += stats.get("attack", 0)
            self._magic += stats.get("magic", 0) or stats.get("spell", 0)
            self._def += stats.get("defense", 0)
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        self.attack = self._atk
        self.magic = self._magic
        self.defense = self._def

    def auto_learn_skills(self):
        klass = REGISTRY.get("class", self.klass)
        if klass:
            self.skills_learned = list(klass.get("skills", []))

    def klass_name(self):
        k = REGISTRY.get("class", self.klass)
        return k.get("name", self.klass) if k else self.klass

    def skill_name(self, skill_id):
        s = REGISTRY.get("skill", skill_id)
        return s.get("name", skill_id) if s else skill_id

    # ------- 经验/升级 -------
    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next():
            self.exp -= self.exp_to_next()
            self.level += 1
            self.recalc_stats()

    def exp_to_next(self):
        return 50 + 40 * (self.level - 1) + (self.level - 1) ** 2

    # ------- 资源 -------
    def spend_resource(self, amount):
        if self.resource >= amount:
            self.resource -= amount
            return True
        return False

    def regen_resource(self, dt):
        self.resource = min(self.max_resource, self.resource + 3 * dt)

    # ------- 交互 -------
    def nearby_interactable(self, world, radius=1.5):
        """返回可交互物体（NPC / 采集物 / 传送门）。"""
        result = []
        for e in world.entities:
            if getattr(e, "interactable", False):
                if e.pos.dist(self.pos) <= e.interact_range + radius:
                    result.append(e)
        return result

    def to_json(self):
        return {
            "x": self.x, "y": self.y,
            "level": self.level, "exp": self.exp,
            "klass": self.klass,
            "hp": self.hp,
            "inventory": self.inventory.to_json(),
            "equipment": {k: (None if v is None else v.to_json())
                          for k, v in self.equipment.items()},
            "skills": self.skills_learned,
            "quests": self.quests,
        }

    @classmethod
    def from_json(cls, data):
        p = cls(data.get("x", 8), data.get("y", 8))
        p.level = data.get("level", 1)
        p.exp = data.get("exp", 0)
        p.klass = data.get("klass", "swordsman")
        p.auto_level_base_stats()
        p.inventory = Inventory.from_json(data.get("inventory") or {"gold": 0, "slots": []})
        eq = data.get("equipment") or {}
        for k, v in eq.items():
            p.equipment[k] = ItemStack.from_json(v) if v else None
        p.skills_learned = data.get("skills", [])
        p.quests = data.get("quests", {})
        p.recalc_stats()
        p.hp = data.get("hp", p.max_hp)
        return p
