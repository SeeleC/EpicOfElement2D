# -*- coding: utf-8 -*-
"""静态地形层：区块贴图烘焙 + 缓存（精细地图版 v2）。

修复上一版的三个实测问题：
  1. 白缝：pyglet get_texture() 默认在纹理四周留 1px 未初始化的内部 border，
     Sprite 采样边缘会采进残留 -> 几乎每个区块贴图边缘都白缝。
     本版 border=0 + NEAREST + 绘制前强制过滤 + POT 填充区补色 + 自带出血边。
  2. 卡顿：新入视野区块在渲染帧内同步“生成+烘焙”。本版配合
     game._warm_terrain() 在移动前提前预热，把开销摊到多帧。
  3. 高度差不明显：烘焙加入坡度明暗 + 崖边描边 + 水岸浪线。
"""
import pyglet
import pyglet.gl as gl

from . import config
from . import noise
from .registry import REGISTRY
from .world import CHUNK_SIZE, _BLOCKED_TILES

_TILE_COLORS = {
    "grass": (96, 148, 64), "grass2": (84, 134, 58), "tallgrass": (72, 118, 52),
    "dirt": (120, 96, 70),
    "snow": (222, 230, 238), "snow2": (206, 216, 226),
    "waste": (72, 82, 92), "waste2": (60, 70, 80),
    "rock": (120, 116, 110), "mountain": (96, 92, 88),
    "water": (58, 108, 168), "water_deep": (34, 68, 128),
}
GROUND_DETAIL = {
    "tuft": (86, 138, 66), "dry_tuft": (140, 128, 82), "flower": (228, 118, 180),
    "pebble": (140, 138, 132), "crack": (60, 82, 52), "moss": (66, 118, 66),
    "snow_puff": (238, 242, 248), "ash": (56, 62, 72), "water_ripple": (120, 170, 215),
}
_DETAIL_TABLE = {
    "grass":      (("tuft", 0.30), ("flower", 0.06), ("pebble", 0.04), ("moss", 0.08)),
    "grass2":     (("tuft", 0.26), ("flower", 0.10), ("moss", 0.06)),
    "tallgrass":  (("tuft", 0.42), ("flower", 0.05)),
    "dirt":       (("pebble", 0.14), ("dry_tuft", 0.10), ("crack", 0.06)),
    "snow":       (("snow_puff", 0.22), ("pebble", 0.04)),
    "snow2":      (("snow_puff", 0.18), ("pebble", 0.05)),
    "waste":      (("ash", 0.16), ("crack", 0.10)),
    "waste2":     (("ash", 0.20),),
    "water":      (("water_ripple", 0.10),),
    "water_deep": (("water_ripple", 0.12),),
    "mountain":   (("pebble", 0.20), ("crack", 0.16)),
    "rock":       (("pebble", 0.18), ("crack", 0.10)),
}


def _clamp(v):
    return 0 if v < 0 else (255 if v > 255 else v)


def _mottle(wx, wy, fx, fy, seed):
    ppt = config.BAKE_PX_PER_TILE
    sx = wx + (fx + 0.5) / ppt
    sy = wy + (fy + 0.5) / ppt
    n = noise.value_noise(sx * config.DETAIL_SCALE * 2.2,
                          sy * config.DETAIL_SCALE * 2.2, seed + 777)
    return int((n - 0.5) * 20)


def _subcell_detail(tile, wx, wy, su, sv, seed):
    table = _DETAIL_TABLE.get(tile)
    if not table:
        return None
    ppt = config.BAKE_PX_PER_TILE
    sub = config.DETAIL_SUBCELL
    cx = wx + (su * sub + sub / 2.0) / ppt
    cy = wy + (sv * sub + sub / 2.0) / ppt
    n = noise.value_noise(cx * 0.9, cy * 0.9, seed + 4242)
    if n > 0.70:
        return None
    n2 = noise.value_noise(cx * 1.7 + 9.1, cy * 1.7 - 3.3, seed + 4242)
    total = sum(w for _, w in table)
    acc = n2 * total
    for kind, w in table:
        acc -= w
        if acc <= 0:
            return GROUND_DETAIL.get(kind)
    return GROUND_DETAIL.get(table[-1][0])


def bake_chunk_texture(chunk, world):
    """把区块静态地面烘焙成 512x512 贴图（坡度明暗 / 崖边 / 水岸浪线）。

    布局：内容区 258px（区块 256 + 上下各 1px 出血边）放在贴图 [0,258)，
    [258,512) 用最边缘颜色填充，保证 2 的幂填充区也是有效颜色。
    贴图第 0 行 = 区块底边下方 1px（底部出血），区块第 0 行从 py=1 开始，
    与 Sprite 自下而上的纹理坐标一致，且与世界坐标严格对齐（无 2px 偏移）。
    """
    ppt = config.BAKE_PX_PER_TILE
    sub = config.DETAIL_SUBCELL
    interior = CHUNK_SIZE * ppt          # 256
    bleed = 1
    content = interior + 2 * bleed       # 258
    size = 512                           # POT
    ox, oy = chunk.world_origin()
    biome = REGISTRY.get("biome", chunk.biome) or {}
    tile_colors = biome.get("tile_colors") or {}
    ground = biome.get("colors", {}).get("ground", (96, 148, 64))
    edge = biome.get("colors", {}).get("edge", (70, 110, 50))
    tiles = chunk.tiles[0] if chunk.tiles else None

    def tile_of(wx, wy):
        lx = wx - ox
        ly = wy - oy
        if tiles is not None and 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE:
            return tiles[ly][lx]
        return world.tile_for(wx, wy)    # 出血/邻居用确定性查询

    def color_of(tile):
        if tile in tile_colors:
            return tuple(tile_colors[tile])
        if tile in _TILE_COLORS:
            return _TILE_COLORS[tile]
        return ground if tile not in _BLOCKED_TILES else edge

    # 网格：下标 i 对应世界偏移 i - OFF，覆盖 [oy-2, oy+17]，N=20
    N = CHUNK_SIZE + 4                   # 20
    OFF = 2
    hgrid = [[0.0] * N for _ in range(N)]
    tgrid = [[None] * N for _ in range(N)]
    for ly in range(N):
        wy = oy + ly - OFF
        for lx in range(N):
            wx = ox + lx - OFF
            hgrid[ly][lx] = world.height_at(wx, wy)
            tgrid[ly][lx] = tile_of(wx, wy)

    def H(ly, lx):                       # 越界 clamp（只影响最外圈阴影）
        if ly < 0: ly = 0
        elif ly >= N: ly = N - 1
        if lx < 0: lx = 0
        elif lx >= N: lx = N - 1
        return hgrid[ly][lx]

    def T(ly, lx):
        if ly < 0: ly = 0
        elif ly >= N: ly = N - 1
        if lx < 0: lx = 0
        elif lx >= N: lx = N - 1
        return tgrid[ly][lx]

    # 子格细节（草丛/花/碎石）—— 只覆盖区块主体
    nsub = interior // sub
    det_colors = {}
    for sv in range(nsub):
        wy = oy + (sv * sub + sub // 2 - bleed) // ppt
        for su in range(nsub):
            wx = ox + (su * sub + sub // 2 - bleed) // ppt
            det = _subcell_detail(tile_of(wx, wy), wx, wy, su, sv, world.seed)
            if det:
                det_colors[(su, sv)] = det

    HILL = config.HILL_SHADE
    CDELTA = config.CLIFF_H_DELTA
    CDARK = config.CLIFF_DARKEN
    FOAM = config.SHORE_FOAM
    stride = size * 4
    buf = bytearray(size * size * 4)

    # 逐像素填充：py=0 为底部出血，py=1..256 为区块 16 行，py=257 顶部出血
    for py in range(content):
        ly = (py - bleed) // ppt          # -1..16
        gy = ly + OFF                     # 1..18
        fy = (py - bleed) % ppt
        sv = py // sub
        for px in range(content):
            lx = (px - bleed) // ppt
            gx = lx + OFF
            fx = (px - bleed) % ppt
            tile = tgrid[gy][gx]
            r, g, b = color_of(tile)

            # 坡度明暗
            h0 = hgrid[gy][gx]
            light = (4 * h0 - H(gy, gx + 1) - H(gy, gx - 1)
                     - H(gy + 1, gx) - H(gy - 1, gx)) * HILL
            r = _clamp(r + int(light * 255))
            g = _clamp(g + int(light * 255))
            b = _clamp(b + int(light * 255))

            # 崖边描边（低处一侧）
            if h0 - H(gy, gx + 1) > CDELTA and fx == ppt - 1:
                r = _clamp(r - int(255 * CDARK)); g = _clamp(g - int(255 * CDARK)); b = _clamp(b - int(255 * CDARK))
            if h0 - H(gy, gx - 1) > CDELTA and fx == 0:
                r = _clamp(r - int(255 * CDARK)); g = _clamp(g - int(255 * CDARK)); b = _clamp(b - int(255 * CDARK))
            if h0 - H(gy + 1, gx) > CDELTA and fy == ppt - 1:
                r = _clamp(r - int(255 * CDARK)); g = _clamp(g - int(255 * CDARK)); b = _clamp(b - int(255 * CDARK))
            if h0 - H(gy - 1, gx) > CDELTA and fy == 0:
                r = _clamp(r - int(255 * CDARK)); g = _clamp(g - int(255 * CDARK)); b = _clamp(b - int(255 * CDARK))

            # 水岸浪线：与陆地相邻的水格混入浅色，让碰撞边界肉眼可见
            if tile in ("water", "water_deep"):
                if (T(gy, gx + 1) not in _BLOCKED_TILES or
                        T(gy, gx - 1) not in _BLOCKED_TILES or
                        T(gy + 1, gx) not in _BLOCKED_TILES or
                        T(gy - 1, gx) not in _BLOCKED_TILES):
                    r = _clamp(r + (235 - r) * FOAM)
                    g = _clamp(g + (226 - g) * FOAM)
                    b = _clamp(b + (238 - b) * FOAM)

            det = det_colors.get((px // sub, sv))
            if det:
                r = (r + det[0]) // 2; g = (g + det[1]) // 2; b = (b + det[2]) // 2

            m = _mottle(ox + lx, oy + ly, fx, fy, world.seed)
            r = _clamp(r + m); g = _clamp(g + m); b = _clamp(b + m)

            idx = py * stride + px * 4
            buf[idx] = r; buf[idx + 1] = g; buf[idx + 2] = b; buf[idx + 3] = 255

    # POT 填充区 [258,512) 补最右/最上颜色，避免白色缝
    for py in range(size):
        row_base = py * stride
        if py >= content:
            buf[row_base:row_base + stride] = buf[(content - 1) * stride:
                                                  (content - 1) * stride + stride]
            continue
        last_col = (content - 1) * 4
        for px in range(content, size):
            idx = row_base + px * 4
            buf[idx:idx + 3] = buf[row_base + last_col:row_base + last_col + 3]
            buf[idx + 3] = 255

    image = pyglet.image.ImageData(size, size, "RGBA", bytes(buf), pitch=stride)
    tex = image.get_texture()
    try:
        tex.border = 0
    except Exception:
        pass
    tex.min_filter = gl.GL_NEAREST
    tex.mag_filter = gl.GL_NEAREST
    return tex.get_region(0, 0, content, content)


class TerrainCache:
    """区块地面贴图缓存：TextureRegion + Sprite 一并缓存，LRU 淘汰。"""

    def __init__(self, capacity=96):
        self.capacity = capacity
        self._items = {}
        self._order = []

    def _touch(self, key):
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)
        while len(self._order) > self.capacity:
            old = self._order.pop(0)
            self._items.pop(old, None)

    def get(self, chunk, world):
        key = (chunk.cx, chunk.cy)
        item = self._items.get(key)
        if item is not None:
            self._touch(key)
            return item
        region = bake_chunk_texture(chunk, world)
        sprite = pyglet.sprite.Sprite(region)
        sprite.scale = config.SPRITE_SCALE
        item = (region, sprite)
        self._items[key] = item
        self._touch(key)
        return item

    def clear(self):
        self._items.clear()
        self._order.clear()