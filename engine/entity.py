# -*- coding: utf-8 -*-
"""逻辑实体基类。

玩家、怪物、NPC、投射物都继承自 Entity。
实体拥有: 位置 / 速度 / 生命 / 朝向 / 受击 / 状态。
材质渲染统一使用「程序化图标/色块」，遵循饥荒式俯视风格。
"""
import math
from .vector2 import Vec2


class Entity:
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1.0         # 水平朝向: 1=右, -1=左
        self.alive = True

        self.max_hp = 1
        self.hp = 1
        self.max_resource = 100    # 法力/架势
        self.resource = 100
        self.speed = 2.0

        self.hit_timer = 0.0       # 受击硬直剩余时间
        self.status = {}           # 状态: {'restrain': t} 等
        self.knockx = 0.0
        self.knocky = 0.0

        # 交互 / 归属
        self.interactable = False
        self.interact_range = 1.5
        self.parent_obj = None     # 归属逻辑对象（如所属 NPC）

    # ------- 属性 -------
    @property
    def pos(self):
        return Vec2(self.x, self.y)

    def take_damage(self, amount, source=None):
        if not self.alive:
            return
        self.hp -= amount
        self.hit_timer = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.on_death(source)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + max(0, amount))

    def add_status(self, key, duration):
        if duration > 0:
            self.status[key] = duration

    def update_status(self, dt):
        for k in list(self.status.keys()):
            self.status[k] -= dt
            if self.status[k] <= 0:
                del self.status[k]

    def is_stunned(self):
        return "stun" in self.status or self.hit_timer > 0 and False

    def on_death(self, source=None):
        """子类覆写，用于掉落、经验、任务判定。"""
        pass

    # ------- 移动（带世界碰撞） -------
    def move(self, dx, dy, world, dt):
        """带碰撞的移动：分别沿 X / Y 移动，检测脚下的可走性。"""
        nx = self.x + dx
        ny = self.y + dy
        marg = 0.3
        # X 轴
        if self.can_stand(nx, self.y, world, marg):
            self.x = nx
        else:
            self.x = self.snap_x(nx, world)
        # Y 轴
        if self.can_stand(self.x, ny, world, marg):
            self.y = ny
        else:
            self.y = self.snap_y(ny, world)

    def above(self, wx, wy, world, z=0):
        return True

    def can_stand(self, wx, wy, world, marg=0.3):
        x0, y0 = int(wx - marg), int(wy - marg)
        x1, y1 = int(wx + marg), int(wy + marg)
        for ix in range(x0, x1 + 1):
            for iy in range(y0, y1 + 1):
                if not world.is_walkable(ix, iy):
                    return False
        return True

    def snap_x(self, nx, world):
        # 撞墙后贴墙
        if abs(nx - round(nx)) < 0.1 or not self.alive:
            return self.x
        # 尝试把 x 吸附到最近的可行格边界
        return self.x

    def snap_y(self, ny, world):
        return self.y

    def update(self, dt, world=None):
        self.update_status(dt)
        if self.hit_timer > 0:
            self.hit_timer -= dt
        if self.knockx or self.knocky:
            kx, ky = self.knockx, self.knocky
            self.x += kx * dt
            self.y += ky * dt
            self.knockx *= (1 - 8 * dt)
            self.knocky *= (1 - 8 * dt)
            if abs(self.knockx) < 0.01:
                self.knockx = 0
            if abs(self.knocky) < 0.01:
                self.knocky = 0

    def apply_knockback(self, dx, dy, power):
        self.knockx += dx * power
        self.knocky += dy * power
