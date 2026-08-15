# -*- coding: utf-8 -*-
"""投射物系统：火球 / 冰枪 / 箭矢 / 穿裂箭。

由技能触发生成，朝目标方向飞行，命中造成伤害并可能有爆炸/穿透。
"""
import math
from .entity import Entity
from .vector2 import Vec2


class Projectile(Entity):
    def __init__(self, kind, x, y, dx, dy, damage=10, speed=8.0,
                 range=8, owner=None, pierce=False, radius=0.0,
                 skill=None, hit_effects=None):
        super().__init__(x, y)
        self.kind = kind
        self.dx = dx
        self.dy = dy
        d = math.hypot(dx, dy) or 1
        self.vx = dx / d * speed
        self.vy = dy / d * speed
        self.damage = damage
        self.speed = speed
        self.max_range = range
        self.travel = 0.0
        self.owner = owner
        self.pierce = pierce
        self.radius = radius
        self.skill = skill or {}
        self.hit_effects = hit_effects or {}
        self.hit_ids = set()

    @property
    def is_friendly(self):
        return getattr(self.owner, "klass", None) is not None

    def update(self, dt, world):
        if not self.alive:
            return
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        self.travel += math.hypot(self.vx * dt, self.vy * dt)
        if self.travel > self.max_range or not world.is_walkable(int(nx), int(ny)):
            self.alive = False
            self.trigger_explosion(world)
            return False
        self.x, self.y = nx, ny
        return True

    def try_hit(self, target):
        """尝试命中某个实体。返回是否命中。"""
        if id(target) in self.hit_ids:
            return False
        if isinstance(self.owner, type(target)) and getattr(target, "klass", None) and getattr(self.owner, "klass", None):
            return False  # 不攻击友方玩家
        if target.parent_obj is not None and self.owner is not None:
            pass
        dist = Vec2(self.x, self.y).dist(target.pos)
        hit_r = 0.6 + self.radius
        if dist <= hit_r:
            self.hit_ids.add(id(target))
            dmg = self.damage
            target.take_damage(dmg, self.owner)
            target.apply_knockback(self.dx, self.dy, 1.5)
            # 效果
            if self.hit_effects.get("float"):
                target.add_status("stun", self.hit_effects["float"])
            if self.hit_effects.get("slow"):
                target.add_status("restrain", self.hit_effects["slow"])
            if self.hit_effects.get("burn"):
                target.add_status("burn", 3.0)
            self.trigger_explosion(world)
            return True
        return False

    def trigger_explosion(self, world):
        if self.radius > 0 and world is not None and hasattr(world, "apply_aoe"):
            world.apply_aoe(self.x, self.y, self.radius,
                            self.damage * 0.5, iface=self.owner)
