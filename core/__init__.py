# -*- coding: utf-8 -*-
"""
core 包 —— 基础系统层
======================
相机(camera) / 动画(animation) / 粒子(particle) / 音效(sound) / 存档(save)。
这些组件与具体玩法无关，是场景、实体、UI 共用的“基础设施”。

统一导出，方便 `from core import Camera, ParticleSystem, ...`。
"""

from core.camera import Camera
from core.animation import Animation, Animator, SpriteSheet, placeholder_anim
from core.particle import Particle, ParticleSystem
from core.sound import SoundManager, sound_manager
from core.save import SaveManager, save_manager

__all__ = [
    "Camera",
    "Animation", "Animator", "SpriteSheet", "placeholder_anim",
    "Particle", "ParticleSystem",
    "SoundManager", "sound_manager",
    "SaveManager", "save_manager",
]