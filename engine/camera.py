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
    # 世界坐标 Y 向上（W/上 使 y 增大、画面向上移），故转换时对屏幕 Y 取反，
    # 使「世界向上移动」显示为「屏幕上方向上」，修正原先上下移动颠倒的问题。
    def world_to_screen(self, wx, wy):
        px = (wx - self.pos.x) * config.TILE + self.width / 2
        py = self.height / 2 - (wy - self.pos.y) * config.TILE
        return px, py

    def screen_to_world(self, sx, sy):
        wx = (sx - self.width / 2) / config.TILE + self.pos.x
        wy = self.pos.y - (sy - self.height / 2) / config.TILE
        return wx, wy
