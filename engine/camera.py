# -*- coding: utf-8 -*-
"""摄像机：把世界坐标转换为屏幕坐标，带平滑跟随目标。"""
from . import config
from .vector2 import Vec2


class Camera:
    def __init__(self, width=None, height=None):
        self.width = width or config.Graphics.WINDOW_W
        self.height = height or config.Graphics.WINDOW_H
        self.pos = Vec2()          # 世界坐标（场景中心对准）
        self.target = None

    def attach(self, target):
        self.target = target

    def update(self, dt):
        if self.target is not None:
            tx, ty = self.target.x, self.target.y
            # 世界坐标以格子为单位，屏幕以像素为单位，* TILE 获得像素中心
            self.pos.x += (tx - self.pos.x) * config.Graphics.CAMERA_LERP
            self.pos.y += (ty - self.pos.y) * config.Graphics.CAMERA_LERP

    # 世界坐标(格子) -> 屏幕像素（左上角原点，Y 向下）
    def world_to_screen(self, wx, wy):
        px = (wx - self.pos.x) * config.TILE + self.width / 2
        py = (wy - self.pos.y) * config.TILE + self.height / 2
        return px, py

    def screen_to_world(self, sx, sy):
        wx = (sx - self.width / 2) / config.TILE + self.pos.x
        wy = (sy - self.height / 2) / config.TILE + self.pos.y
        return wx, wy
