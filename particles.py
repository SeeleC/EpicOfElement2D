# -*- coding: utf-8 -*-
"""
粒子系统（particles.py）
========================
纯几何粒子：命中火花、元素特效、死亡爆裂、落地尘土。
不依赖任何美术资源。
"""

import math
import random

import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity


class ParticleSystem:
    ELEMENT_COLORS = {
        "fire": (255, 120, 40), "ice": (140, 200, 255),
        "thunder": (255, 255, 120), "earth": (170, 140, 90),
        "dark": (150, 90, 190), "holy": (255, 240, 200),
        "wind": (180, 255, 200),
    }

    def __init__(self):
        self.particles = []

    def spawn(self, x, y, vx, vy, life, color, size, gravity=0.0):
        self.particles.append(Particle(x, y, vx, vy, life, color, size, gravity))

    def hit_effect(self, x, y, color=(255, 255, 255), is_crit=False):
        n = 18 if is_crit else 10
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(50, 200 if is_crit else 140)
            self.spawn(x, y, math.cos(ang) * sp, math.sin(ang) * sp - 40,
                       random.uniform(0.2, 0.5), color,
                       random.randint(2, 4), gravity=300)

    def element_effect(self, x, y, element):
        c = self.ELEMENT_COLORS.get(element, (255, 255, 255))
        for _ in range(8):
            self.spawn(x + random.uniform(-14, 14), y + random.uniform(-14, 14),
                       random.uniform(-30, 30), random.uniform(-90, -20),
                       random.uniform(0.3, 0.6), c, random.randint(3, 5))

    def death_burst(self, x, y, color):
        for _ in range(20):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(60, 240)
            self.spawn(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                       random.uniform(0.4, 0.9), color,
                       random.randint(3, 6), gravity=400)

    def dust(self, x, y, color=(150, 150, 160)):
        self.spawn(x + random.uniform(-10, 10), y + 4,
                   random.uniform(-30, 30), random.uniform(-24, 0),
                   random.uniform(0.3, 0.5), color, random.randint(2, 3))

    # ------------------------------------------------------------------
    def update(self, dt):
        keep = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            keep.append(p)
        self.particles = keep

    def draw(self, surface, cam):
        for p in self.particles:
            sx, sy = cam.apply_point(p.x, p.y)
            fade = max(0.0, p.life / p.max_life)
            size = max(1, int(p.size * (0.5 + 0.5 * fade)))
            pygame.draw.circle(surface, p.color, (int(sx), int(sy)), size)