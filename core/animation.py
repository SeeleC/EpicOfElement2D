# -*- coding: utf-8 -*-
"""
动画系统（animation.py）
========================
提供逐帧动画的三个组件：
  - Animation：一组帧 + 播放速度 + 循环/不循环；
  - Animator：角色状态机驱动的动画管理器（站立/跑/跳/攻击…）；
  - SpriteSheet：精灵图切割工具（从一张大图切出帧）。

没有美术资源时，可用 placeholder_anim() 生成纯色占位动画先跑起来。
"""

import pygame

from utils import make_surface


class Animation:
    """单段逐帧动画。"""

    def __init__(self, frames, fps=8, loop=True):
        self.frames = list(frames)
        self.fps = max(1, fps)
        self.loop = loop
        self.time = 0.0
        self.playing = True
        self.finished = False

    @property
    def duration(self):
        return len(self.frames) / self.fps

    def reset(self):
        self.time = 0.0
        self.playing = True
        self.finished = False
        return self

    def update(self, dt):
        if not self.playing or not self.frames:
            return
        self.time += dt
        if self.loop:
            self.time %= self.duration
        elif self.time >= self.duration:
            self.time = self.duration
            self.playing = False
            self.finished = True

    def get_frame(self):
        if not self.frames:
            return None
        idx = min(int(self.time * self.fps), len(self.frames) - 1)
        return self.frames[idx]

    def play(self):
        self.playing = True
        return self

    def stop(self):
        self.playing = False
        return self


class Animator:
    """按状态切换动画（state -> Animation）。"""

    def __init__(self):
        self.anims = {}
        self.state = None
        self.last_state = None

    def add(self, state, animation):
        self.anims[state] = animation
        return self

    def play(self, state):
        """切换到指定状态；相同状态不打断当前动画。"""
        if state not in self.anims:
            return self
        if state != self.state:
            self.last_state = self.state
            self.anims[state].reset()
            self.state = state
        return self

    def update(self, dt):
        anim = self.anims.get(self.state)
        if anim:
            anim.update(dt)

    def get_frame(self):
        anim = self.anims.get(self.state)
        return anim.get_frame() if anim else None

    @property
    def finished(self):
        anim = self.anims.get(self.state)
        return bool(anim and anim.finished)


class SpriteSheet:
    """精灵图切割：把一张大图按等宽高等距切成帧。"""

    def __init__(self, surface, frame_w, frame_h):
        self.surface = surface
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.cols = max(1, surface.get_width() // frame_w)
        self.rows = max(1, surface.get_height() // frame_h)

    def get_frame(self, col, row=0):
        rect = pygame.Rect(col * self.frame_w, row * self.frame_h,
                           self.frame_w, self.frame_h)
        return self.surface.subsurface(rect)

    def get_animation(self, row, cols, fps=8, loop=True):
        """按行取连续列作为一帧动画。cols: 列号列表或 (start, end)。"""
        if isinstance(cols, tuple):
            cols = range(cols[0], cols[1])
        return Animation([self.get_frame(c, row) for c in cols],
                         fps=fps, loop=loop)


def placeholder_anim(color, size=(48, 48), frames=4, fps=8, loop=True):
    """生成占位动画：纯色块上有一个移动的小圆点，方便先跑通逻辑。"""
    frames_l = []
    for i in range(frames):
        surf = make_surface(size, color)
        t = i / max(1, frames - 1)
        cx = int(8 + t * (size[0] - 16))
        cy = size[1] // 2
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 5)
        frames_l.append(surf)
    return Animation(frames_l, fps=fps, loop=loop)