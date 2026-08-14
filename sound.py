# -*- coding: utf-8 -*-
"""
音效系统（sound.py）
====================
无外部音频文件时用「程序合成」生成简单音效（正弦/方波/噪声）。
音量分三档：主 / 音效 / 音乐。BGM 可加载 assets/sound/*.ogg，缺失则静默。
"""

import array
import math
import os
import random

import pygame

RATE = 22050


class SoundManager:
    def __init__(self):
        self._ok = False
        self.master = 0.8
        self.sfx_vol = 1.0
        self.music_vol = 0.6
        self._cache = {}
        self._music_name = None
        try:
            pygame.mixer.pre_init(RATE, -16, 2, 512)
            pygame.mixer.init()
            self._ok = True
        except pygame.error as exc:
            print(f"[sound] 音频初始化失败：{exc}")

    # ------------------------------------------------------------------
    def _stereo(self, mono_samples):
        buf = array.array("h")
        for s in mono_samples:
            buf.append(s)
            buf.append(s)
        return buf.tobytes()

    def _synth(self, freq, duration, volume=0.5, wave="sine", decay=True):
        if not self._ok:
            return None
        n = int(RATE * duration)
        out = []
        for i in range(n):
            t = i / RATE
            if wave == "sine":
                v = math.sin(2 * math.pi * freq * t)
            elif wave == "square":
                v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            elif wave == "saw":
                v = 2.0 * ((freq * t) % 1.0) - 1.0
            else:  # noise
                v = random.uniform(-1.0, 1.0)
            env = (1.0 - t / duration) if decay else 1.0
            out.append(int(v * env * volume * 32767))
        return pygame.mixer.Sound(buffer=self._stereo(out))

    def _get(self, name):
        if name in self._cache:
            return self._cache[name]
        snd = None
        if name == "hit":
            snd = self._synth(180, 0.08, 0.5, "square")
        elif name == "crit":
            snd = self._synth(300, 0.12, 0.6, "saw")
        elif name == "kill":
            snd = self._synth(90, 0.25, 0.5, "saw")
        elif name == "coin":
            snd = self._synth(880, 0.09, 0.35, "sine")
            snd2 = self._synth(1320, 0.10, 0.35, "sine")
            if snd and snd2:
                s = pygame.mixer.Sound(buffer=snd.get_raw() + snd2.get_raw())
                snd = s
        elif name == "levelup":
            snd = self._synth(523, 0.12, 0.4, "sine")
        elif name == "jump":
            snd = self._synth(220, 0.12, 0.3, "sine", decay=False)
        elif name == "dodge":
            snd = self._synth(600, 0.15, 0.3, "noise")
        elif name == "skill":
            snd = self._synth(160, 0.2, 0.5, "saw")
        elif name == "hurt":
            snd = self._synth(120, 0.2, 0.5, "square")
        elif name == "buy":
            snd = self._synth(660, 0.08, 0.4, "sine")
        elif name == "sell":
            snd = self._synth(990, 0.08, 0.4, "sine")
        elif name == "quest":
            snd = self._synth(523, 0.15, 0.4, "sine")
        elif name == "ui":
            snd = self._synth(440, 0.06, 0.3, "sine")
        elif name == "error":
            snd = self._synth(160, 0.12, 0.4, "square")
        elif name == "death":
            snd = self._synth(80, 0.7, 0.5, "saw")
        self._cache[name] = snd
        return snd

    # ------------------------------------------------------------------
    def play(self, name, volume=1.0):
        if not self._ok:
            return
        snd = self._get(name)
        if snd:
            snd.set_volume(min(1.0, self.master * self.sfx_vol * volume))
            snd.play()

    def play_music(self, name):
        if not self._ok or name == self._music_name:
            return
        path = os.path.join("assets", "sound", f"{name}.ogg")
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.master * self.music_vol)
            pygame.mixer.music.play(-1)
            self._music_name = name

    def stop_music(self):
        if self._ok:
            pygame.mixer.music.stop()
        self._music_name = None

    # ------------------------------------------------------------------
    def set_master(self, v):
        self.master = max(0.0, min(1.0, v))

    def set_sfx_volume(self, v):
        self.sfx_vol = max(0.0, min(1.0, v))

    def set_music_volume(self, v):
        self.music_vol = max(0.0, min(1.0, v))
        if self._ok and self._music_name:
            pygame.mixer.music.set_volume(self.master * self.music_vol)