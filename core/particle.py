# -*- coding: utf-8 -*-
"""
粒子系统（particle.py）
=======================
轻量 2D 粒子：命中火花、元素特效、受击喷血、范围爆裂等。
粒子在世界坐标中运动，绘制时通过摄像机偏移换算到屏幕。

用法：
    ps = ParticleSystem()
    ps.hit_effect(x, y, (255, 120, 60), is_crit=True)   # 命中特效
    ps.element_effect(x, y, "fire")                     # 元素特效
    ps.update(dt)
    ps.draw(screen, cam.offset())
"""

import math
import random

import pygame

from config import ELEMENTS


class Particle:
    """单个粒子。"""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life",
                 "size", "color", "gravity", "drag", "fade", "shape")

    def __init__(self, x, y, vx, vy, life, size, color,
                 gravity=0.0, drag=1.0, fade=True, shape="circle"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.gravity = gravity
        self.drag = drag
        self.fade = fade
        self.shape = shape

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False
        # 阻力（帧率无关的指数衰减）
        k = 1.0 - math.exp(-self.drag * dt)
        self.vx -= self.vx * k
        self.vy -= self.vy * k
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True

    def draw(self, surface, ox, oy):
        px, py = self.x - ox, self.y - oy
        t = max(0.0, self.life / self.max_life)
        size = max(1, int(self.size * t if self.fade else self.size))
        color = self.color
        if self.fade:
            alpha = int(255 * t)
            color = (*color[:3], alpha)
        if self.shape == "rect":
            rect = pygame.Rect(px - size / 2, py - size / 2, size, size)
            pygame.draw.rect(surface, color, rect)
        else:
            pygame.draw.circle(surface, color, (int(px), int(py)), size)


class ParticleSystem:
    MAX_PARTICLES = 600  # 数量上限，防止爆内存

    def __init__(self):
        self.particles = []

    # ------------------------------------------------------------------
    # 生成
    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, gravity=0.0,
              drag=1.0, fade=True, shape="circle"):
        if len(self.particles) >= self.MAX_PARTICLES:
            return
        self.particles.append(Particle(x, y, vx, vy, life, size, color,
                                       gravity, drag, fade, shape))

    def burst(self, x, y, count, colors, speed=(30, 220), life=(0.3, 0.9),
              size=(2, 6), gravity=400.0, drag=0.5, angle=None, spread=360.0):
        """向四周喷射一批粒子。"""
        for _ in range(count):
            sp = random.uniform(*speed)
            a = random.uniform(0, math.radians(spread))
            if angle is not None:
                a = angle + random.uniform(-0.4, 0.4)
            vx, vy = math.cos(a) * sp, math.sin(a) * sp - 60
            self.spawn(x, y, vx, vy,
                       random.uniform(*life),
                       random.uniform(*size),
                       random.choice(colors),
                       gravity=gravity, drag=drag)

    def ring(self, x, y, count, colors, radius_speed=(80, 180), life=0.5,
             size=(2, 5)):
        """环形扩散（冲击波/爆炸特效）。"""
        for i in range(count):
            a = math.radians(360.0 * i / count)
            sp = random.uniform(*radius_speed)
            self.spawn(x, y, math.cos(a) * sp, math.sin(a) * sp,
                       life, random.uniform(*size), random.choice(colors),
                       gravity=0.0, drag=2.0)

    # ------------------------------------------------------------------
    # 常用特效封装
    # ------------------------------------------------------------------
    def hit_effect(self, x, y, color, is_crit=False):
        """近战命中特效；暴击时喷得更多更亮。"""
        self.burst(x, y, 8 if not is_crit else 16,
                   [color, (255, 255, 255) if is_crit else color],
                   speed=(40, 200) if not is_crit else (80, 320),
                   life=(0.15, 0.45), size=(2, 5), gravity=300.0, drag=0.6)
        if is_crit:
            self.ring(x, y, 10, [color], radius_speed=(120, 240), life=0.4)

    def element_effect(self, x, y, element):
        """按元素类型生成对应颜色的特效。"""
        el = ELEMENTS.get(element)
        color = el["color"] if el else (255, 255, 255)
        self.burst(x, y, 12, [color, (255, 255, 255)],
                   speed=(60, 260), life=(0.3, 0.8),
                   size=(2, 6), gravity=200.0, drag=0.6)

    def blood_effect(self, x, y):
        """受击喷血（红色粒子）。"""
        self.burst(x, y, 10, [(200, 40, 40), (150, 25, 25)],
                   speed=(40, 180), life=(0.2, 0.5),
                   size=(2, 4), gravity=500.0, drag=0.3)

    def dust_effect(self, x, y, count=4):
        """落地尘土。"""
        self.burst(x, y, count, [(150, 140, 130), (180, 170, 160)],
                   speed=(20, 90), life=(0.2, 0.5),
                   size=(2, 4), gravity=0.0, drag=1.5)

    # ------------------------------------------------------------------
    # 更新 / 绘制
    # ------------------------------------------------------------------
    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        for p in self.particles:
            p.draw(surface, ox, oy)

    def clear(self):
        self.particles.clear()