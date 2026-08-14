# -*- coding: utf-8 -*-
"""
投射物（projectile.py）
======================
技能 / 怪物的远程弹道：火球、箭矢、暗影球等通用实现。
支持：多段命中(hit_count)、穿透(pierce)、重力、最大射程、元素染色。
"""

import math

import pygame

from config import ELEMENTS


class Projectile:
    def __init__(self, x, y, vx, vy, atk, mult, element, owner,
                 hit_count=1, crit_rate=0.05, crit_dmg=1.5,
                 effects=None, radius=8, color=None, pierce=1,
                 life=2.5, gravity=0.0, max_dist=800):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)

        self.atk = atk
        self.mult = mult
        self.element = element
        self.owner = owner
        self.hit_count = hit_count
        self.crit_rate = crit_rate
        self.crit_dmg = crit_dmg
        self.effects = effects or {}

        self.radius = radius
        el = ELEMENTS.get(element) if element else None
        self.color = color or (el["color"] if el else (255, 220, 120))

        self.pierce = pierce
        self.life = life
        self.gravity = gravity
        self.max_dist = max_dist

        self.traveled = 0.0
        self.dead = False
        self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.hit_set = set()   # 已命中的目标（防止同一目标重复结算）

    def update(self, dt, platforms=()):
        if self.dead:
            return
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.traveled += math.hypot(self.vx * dt, self.vy * dt)
        if self.traveled > self.max_dist:
            self.dead = True
            return
        self.rect.center = (int(self.x), int(self.y))
        for p in platforms:
            if self.rect.colliderect(p):
                self.dead = True
                return

    def draw(self, surface, cam):
        if self.dead:
            return
        sx, sy = cam.apply_point(self.x, self.y)
        pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255),
                           (int(sx), int(sy)), max(2, self.radius - 3))