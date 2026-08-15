# -*- coding: utf-8 -*-
"""轻量二维向量，用于实体移动、渲染坐标。"""
import math


class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        return Vec2(self.x, self.y)

    def length(self):
        return math.hypot(self.x, self.y)

    def normalized(self):
        l = self.length()
        if l == 0:
            return Vec2()
        return Vec2(self.x / l, self.y / l)

    def dist(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def __add__(self, o):
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o):
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s):
        return Vec2(self.x * s, self.y * s)

    __rmul__ = __mul__

    def __repr__(self):
        return f"Vec2({self.x:.1f},{self.y:.1f})"
