# -*- coding: utf-8 -*-
"""
摄像机（camera.py）
===================
2D 横版（DNF 式）世界中，摄像机负责把“世界坐标”换算成“屏幕坐标”：
  - 平滑跟随目标（玩家）；
  - 自动夹紧在地图边界内；
  - 支持受击震动（屏幕抖动）。

用法：
    cam = Camera(WINDOW_WIDTH, WINDOW_HEIGHT, world_w, world_h)
    cam.follow(player.rect, dt)     # 每帧跟随
    cam.shake(6, 0.3)               # 受击/技能命中时抖动
    screen.blit(img, cam.apply_rect(rect))
"""

import math
import random

import pygame


class Camera:
    def __init__(self, view_w, view_h, world_w=0, world_h=0):
        self.view_w = int(view_w)
        self.view_h = int(view_h)
        self.world_w = int(world_w)
        self.world_h = int(world_h)

        # 摄像机左上角在世界中的坐标（float，平滑用）
        self.x = 0.0
        self.y = 0.0

        # 屏幕震动参数
        self.shake_time = 0.0
        self.shake_duration = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = (0, 0)

    # ------------------------------------------------------------------
    # 跟随 / 更新
    # ------------------------------------------------------------------
    def follow(self, target_rect, dt, lerp_factor=0.14):
        """平滑跟随目标矩形（通常传玩家 rect）。"""
        # 目标位置 = 目标中心 - 视口一半
        tx = target_rect.centerx - self.view_w / 2
        ty = target_rect.centery - self.view_h / 2
        # 使用指数平滑，帧率无关
        k = 1.0 - math.exp(-lerp_factor * dt * 60)
        self.x += (tx - self.x) * k
        self.y += (ty - self.y) * k
        self.clamp()

    def clamp(self):
        """把摄像机限制在地图范围内（地图小于视口时居中）。"""
        if self.world_w <= self.view_w:
            self.x = (self.world_w - self.view_w) / 2
        else:
            self.x = max(0, min(self.x, self.world_w - self.view_w))
        if self.world_h <= self.view_h:
            self.y = (self.world_h - self.view_h) / 2
        else:
            self.y = max(0, min(self.y, self.world_h - self.view_h))

    def update(self, dt):
        """更新屏幕震动。"""
        if self.shake_time > 0:
            self.shake_time = max(0.0, self.shake_time - dt)
            # 震动幅度随时间衰减
            power = self.shake_intensity * (self.shake_time / self.shake_duration)
            self.shake_offset = (
                random.uniform(-power, power),
                random.uniform(-power, power),
            )
        else:
            self.shake_offset = (0, 0)

    def shake(self, intensity=6.0, duration=0.25):
        """触发屏幕震动。intensity=最大偏移像素，duration=持续秒数。"""
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)
        self.shake_time = self.shake_duration

    # ------------------------------------------------------------------
    # 坐标换算
    # ------------------------------------------------------------------
    def offset(self):
        """返回当前渲染偏移 (dx, dy)，含震动。"""
        return (self.x + self.shake_offset[0], self.y + self.shake_offset[1])

    def apply_point(self, wx, wy):
        """世界坐标 -> 屏幕坐标。"""
        dx, dy = self.offset()
        return (wx - dx, wy - dy)

    def apply_rect(self, rect):
        """世界矩形 -> 屏幕矩形。"""
        dx, dy = self.offset()
        return rect.move(-dx, -dy)

    def screen_to_world(self, sx, sy):
        """屏幕坐标 -> 世界坐标（鼠标拾取/点击用）。"""
        dx, dy = self.offset()
        return (sx + dx, sy + dy)

    # ------------------------------------------------------------------
    def world_rect(self):
        return pygame.Rect(0, 0, self.world_w, self.world_h)

    def visible_rect(self):
        """当前可见的世界区域（用于裁剪/只渲染屏幕内物体）。"""
        x, y = self.offset()
        return pygame.Rect(x, y, self.view_w, self.view_h)