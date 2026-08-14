# -*- coding: utf-8 -*-
"""
音频管理（sound.py）
===================
集中管理音效与背景音乐：
  - 惰性加载：第一次播放时才加载文件，缺失时自动合成简单音调兜底；
  - 音量分级：主音量 / 音效 / 音乐 独立控制；
  - 兼容无声卡环境（自动降级为“无声”而不崩溃）。

所有音频文件放在 assets/sounds/ 下（.wav / .ogg）。
"""

import math
import os
import struct

import pygame

from config import SND_DIR


class SoundManager:
    def __init__(self, master=0.8, sfx=1.0, music=0.6):
        self.master = float(master)
        self.sfx_vol = float(sfx)
        self.music_vol = float(music)
        self.sounds = {}          # name -> pygame.mixer.Sound
        self._available = False

        # 检查混音器是否可用（无声卡/初始化失败时静默降级）
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self._available = pygame.mixer.get_init() is not None
        except Exception:
            self._available = False

    # ------------------------------------------------------------------
    def _load(self, name):
        """加载音效（首次使用）。失败时尝试合成，再失败则返回 None。"""
        if not self._available:
            return None
        path = os.path.join(SND_DIR, name)
        try:
            snd = pygame.mixer.Sound(path)
        except Exception:
            snd = self._synth(name)
        self.sounds[name] = snd
        return snd

    def _synth(self, name):
        """根据文件名猜测音效类型并合成一个简单音调（兜底方案）。"""
        n = name.lower()
        if "hit" in n or "slash" in n or "crit" in n:
            return self._synth_tone(520, 70, 0.5)
        if "explo" in n or "boom" in n or "burst" in n:
            return self._synth_tone(180, 260, 0.8)
        if "fire" in n:
            return self._synth_tone(720, 120, 0.4)
        if "ice" in n:
            return self._synth_tone(1400, 160, 0.3)
        if "coin" in n or "gold" in n or "pickup" in n:
            return self._synth_tone(900, 90, 0.4)
        if "jump" in n or "dash" in n or "step" in n:
            return self._synth_tone(400, 60, 0.3)
        if "level" in n or "upgrade" in n:
            return self._synth_tone(660, 200, 0.5)
        return self._synth_tone(440, 100, 0.3)

    def _synth_tone(self, freq, ms, volume=0.5):
        """生成 16 位 PCM 单/双声道正弦波音效，无需 numpy。"""
        try:
            init = pygame.mixer.get_init()
            if init is None:
                return None
            rate, _size, channels = init
            n = max(int(rate * ms / 1000), rate // 60)
            attack = max(1, int(rate * 0.004))
            release = max(1, int(rate * 0.02))
            buf = bytearray()
            for i in range(n):
                env = min(1.0, i / attack) * min(1.0, (n - i) / release)
                v = int(math.sin(2 * math.pi * freq * i / rate)
                        * env * volume * 32767)
                if channels >= 2:
                    buf += struct.pack("<hh", v, v)
                else:
                    buf += struct.pack("<h", v)
            return pygame.mixer.Sound(buffer=bytes(buf))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # 播放
    # ------------------------------------------------------------------
    def play(self, name, volume=1.0, loops=0):
        """播放音效。loops=-1 表示循环。"""
        if not self._available:
            return
        snd = self.sounds.get(name)
        if snd is None:
            snd = self._load(name)
        if snd:
            try:
                snd.set_volume(volume * self.sfx_vol * self.master)
                snd.play(loops=loops)
            except pygame.error:
                pass

    def play_music(self, name, volume=1.0, loops=-1):
        """播放背景音乐（assets/sounds/ 下，支持 .ogg/.wav）。"""
        if not self._available:
            return
        path = os.path.join(SND_DIR, name)
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume * self.music_vol * self.master)
            pygame.mixer.music.play(loops=loops)
        except pygame.error:
            pass

    def stop_music(self):
        if self._available:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass

    # ------------------------------------------------------------------
    # 音量
    # ------------------------------------------------------------------
    def set_master(self, v):
        self.master = max(0.0, min(1.0, v))
        if self._available:
            try:
                pygame.mixer.music.set_volume(self.music_vol * self.master)
            except pygame.error:
                pass

    def set_sfx_volume(self, v):
        self.sfx_vol = max(0.0, min(1.0, v))

    def set_music_volume(self, v):
        self.music_vol = max(0.0, min(1.0, v))
        if self._available:
            try:
                pygame.mixer.music.set_volume(self.music_vol * self.master)
            except pygame.error:
                pass


# 全局共享实例（场景 / UI 直接 import 使用）
sound_manager = SoundManager()