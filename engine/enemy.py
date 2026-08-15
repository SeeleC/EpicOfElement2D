# -*- coding: utf-8 -*-
"""敌人生成 / AI / 掉落。

Enemy 依据怪物数据包(monster.json)创建，拥有简单追逐与攻击 AI。
死亡时按 drops 概率掉落物品并给予经验并通知任务系统。
"""
import random
from .entity import Entity
from .vector2 import Vec2
from .registry import REGISTRY
from . import config


class Enemy(Entity):
    def __init__(self, monster_id, x=0.0, y=0.0):
        super().__init__(x, y)
        self.monster_id = monster_id
        mp = self.reload()
        self.base = mp
        self.spawn_x, self.spawn_y = float(x), float(y)
        self.wander_timer = 0.0
        self.atk_cd = 0.0
        self.aggro_range = 6.0
        self.on_death_cb = None     # 由 Game 设置，回报任务/经验

    def reload(self):
        mp = REGISTRY.get("monster", self.monster_id) or {}
        self.max_hp = mp.get("hp", 100)
        self.hp = self.max_hp
        self.attack = mp.get("attack", 10)
        self.speed = mp.get("speed", 2.0)
        self.exp_reward = mp.get("exp", 10)
        self.gold_range = mp.get("gold", [0, 0])
        self.drops = mp.get("drops", [])
        self.aggro = mp.get("aggressive", False)
        self.boss = mp.get("boss", False)
        return mp

    def icon(self):
        return self.base.get("icon", "boar")

    def name(self):
        return self.base.get("name", self.monster_id)

    def damage_to(self, target):
        xd = target.x - self.x
        yd = target.y - self.y
        if abs(xd) > 0.1:
            self.facing = 1 if xd > 0 else -1
        if self.atk_cd > 0:
            self.atk_cd -= 0.016 * 3
        dist = Vec2(self.x, self.y).dist(target.pos)
        if dist < 1.8 and self.atk_cd <= 0:
            self.atk_cd = 1.0
            dmg = self.attack
            target.take_damage(dmg, self)
            return True
        return False

    def update_ai(self, dt, target, world):
        if not self.alive:
            return
        if self.hit_timer > 0:
            self.hit_timer -= dt
        self.update_status(dt)

        if self.atk_cd > 0:
            self.atk_cd -= dt

        if target is None or not target.alive:
            self.wander(dt, world)
            return

        dist = Vec2(self.x, self.y).dist(target.pos)
        if dist > self.aggro_range and self.boss:
            dist = 0  # boss 始终感应

        if dist > 1.6:
            dx = target.x - self.x
            dy = target.y - self.y
            d = (dx**2 + dy**2) ** 0.5
            self.move(dx / d * self.speed * dt, dy / d * self.speed * dt, world, dt)
        else:
            self.damage_to(target)

    def wander(self, dt, world):
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_timer = 2.0 + random.random() * 2
            self.facing = random.randint(-1, 1) or 1
        self.move(self.facing * self.speed * 0.4 * dt, random.uniform(-1, 1) * 0.3 * dt, world, dt)

    def on_death(self, source=None):
        """掉落与回调。"""
        drops = []
        for d in self.drops:
            if random.random() <= d.get("rate", 0.5):
                drops.append((d["id"], random.randint(1, 2)))
        # 金币
        if isinstance(self.gold_range, (list, tuple)) and len(self.gold_range) == 2:
            drops.append(("coin", random.randint(self.gold_range[0], self.gold_range[1])))
        self.loot = drops
        if self.on_death_cb:
            self.on_death_cb(self)

# 方便生成：查找某生物群系的怪物
def spawn_for_biome(biome_id, x, y):
    biome = REGISTRY.get("biome", biome_id) or {}
    spawns = biome.get("spawns") or ["wild_boar"]
    mid = random.choice(spawns)
    return Enemy(mid, x, y)
