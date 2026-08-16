# -*- coding: utf-8 -*-
"""确定性值噪声 / FBM（分形布朗运动）。

用于地图生成的所有连续变化量：
    - 生物群系区域（低频 fbm）  —— 群系呈连续大片斑块而非逐区块随机；
    - 高度图（多层 fbm）       —— 区分 深海/浅滩/陆地/山地；
    - 地面细节（高频噪声）     —— 草丛/花朵/碎石/斑驳 的程序化排布。

全部基于整数坐标的确定性哈希插值：同一种子永远得到相同结果。
因此「生成时用噪声、渲染时用同一种子复算」也能得到一致地形，
无需把静态细节写入存档 —— 保持「按区块轻量持久化」的原设计。
"""
import math


def _hash2(x, y, seed):
    """(x, y, seed) -> [0,1) 的确定性伪随机数（整数坐标）。"""
    h = (x * 374761393 + y * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFFFF) / 0xFFFFFF


def _smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(x, y, seed):
    """网格值噪声（双线性插值）。x,y 可为浮点世界坐标。"""
    x0 = math.floor(x); y0 = math.floor(y)
    fx = x - x0; fy = y - y0
    v00 = _hash2(x0, y0, seed)
    v10 = _hash2(x0 + 1, y0, seed)
    v01 = _hash2(x0, y0 + 1, seed)
    v11 = _hash2(x0 + 1, y0 + 1, seed)
    u = _smooth(fx); v = _smooth(fy)
    a = v00 + (v10 - v00) * u
    b = v01 + (v11 - v01) * u
    return a + (b - a) * v


def fbm(x, y, seed, octaves=4, lacunarity=2.0, gain=0.5):
    """分形布朗运动：多层值噪声叠加，输出约在 [0,1]。"""
    amp = 1.0
    freq = 1.0
    total = 0.0
    norm = 0.0
    for _ in range(octaves):
        total += value_noise(x * freq, y * freq, seed) * amp
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm