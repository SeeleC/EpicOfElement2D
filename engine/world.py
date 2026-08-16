# -*- coding: utf-8 -*-
"""世界 / 地图 / 区块 (World / Chunk)。—— 精细地图版（饥荒式）

相对旧版（每区块随机群系、每格单一纯色）的改进：
    - 生物群系由「低频 FBM 噪声」驱动，连成大片斑块，而非逐区块随机跳变；
    - 高度图（多层 FBM）区分 深海/浅滩/陆地/山地，世界边界可推得非常远：
      WORLD_RADIUS=None 时无限延伸；设置半径则外围退化为海洋形成大陆边缘；
    - 地面带变体（草/高草/泥土斑块）与细节（草丛/花/碎石），视觉接近《饥荒》；
    - 遮挡性装饰（树/岩）可标记 blocked，支持真实走位碰撞（默认关闭）。

设计不变（保持原性能优化策略）：
    - 世界按 16x16 区块懒生成、按区块序列化，只有访问过的区块才持久化；
    - 生成完全确定性：同一 (seed, 世界坐标) 永远得到相同地形，
      静态细节无需写入存档，区块 JSON 依然轻量；
    - 静态地面烘焙进区块贴图并缓存，运行期每帧只重绘可见区块少量精灵。
"""
import random
import math

from . import config
from . import noise
from .registry import REGISTRY

CHUNK_SIZE = 16            # 区块边长（格子数）
MAX_LEVEL = 4              # 最大分层（兼容保留）

# 不可通行方块：默认只有水域挡路。山地/岩地改为可通行高地（饥荒式）。
# 若想让山地重新挡路，把 "mountain" 加回这个集合即可。
_BLOCKED_TILES = {"water", "water_deep", "lava"}


class Chunk:
    """单个区块。保存该区块内所有格子与逻辑实体引用。"""

    def __init__(self, cx, cy, cz=0):
        self.cx = cx
        self.cy = cy
        self.cz = cz
        self.size = CHUNK_SIZE
        self.tiles = None          # tiles[z][y][x] -> tile_id（含变体）
        self.biome = None          # 区块主群系 id
        self.decor = {}            # decor[(x,y)] -> decor_id 装饰物
        self.gather = {}           # gather[(x,y)] -> gather_id 采集物
        self._blocked_decor = set(config.BLOCKING_DECOR)
        self._seed = None
        self.generated = False

    # ------- 坐标换算 -------
    def abs_size(self):
        return CHUNK_SIZE

    def world_origin(self):
        return self.cx * CHUNK_SIZE, self.cy * CHUNK_SIZE

    def local(self, wx, wy):
        ox, oy = self.world_origin()
        return wx - ox, wy - oy

    def ensure_generated(self, world=None):
        if not self.generated:
            self.generate(world)
        return self

    def generate(self, world=None):
        """按世界种子 + 噪声程序化生成地面与装饰。world 提供 seed/噪声。"""
        ox, oy = self.world_origin()
        seed = world.seed if world is not None else (self.cx * 1000003 + self.cy * 9176 + 1)
        self._seed = seed

        self.biome = (world.biome_at(ox + self.size / 2, oy + self.size / 2)
                      if world else self._fallback_biome())

        grid = []
        for yy in range(self.size):
            row = []
            for xx in range(self.size):
                row.append(world.tile_for(ox + xx, oy + yy) if world else "grass")
            grid.append(row)
        self.tiles = {0: grid}

        biome = REGISTRY.get("biome", self.biome) or {}
        self._blocked_decor = set(biome.get("blocked_decor") or config.BLOCKING_DECOR)

        # 装饰物：密度由噪声驱动，只在可走格子上放；出生点附近不放“遮挡性”装饰
        decors = biome.get("decor") or ["tree", "bush"]
        density = float(biome.get("density", 0.05))
        pr = config.SPAWN_PROTECT_RADIUS
        for yy in range(self.size):
            for xx in range(self.size):
                wx, wy = ox + xx, oy + yy
                tile = self.tiles[0][yy][xx]
                if not self._tile_walkable(tile):
                    continue
                if noise.value_noise(wx * 1.7, wy * 1.7, seed + 9001) >= density:
                    continue
                d = random.Random(wx * 31 + wy * 17 + seed).choice(decors) if decors else "tree"
                if d in self._blocked_decor and wx * wx + wy * wy < pr * pr:
                    continue
                self.decor[(xx, yy)] = d

        # 采集物：确定性随机（同区块每次生成一致）
        gathers = biome.get("gather") or []
        if gathers:
            for i in range(3):
                xx = random.Random(seed + ox + oy + i).randrange(self.size)
                yy = random.Random(seed * 7 + ox + oy + i * 3).randrange(self.size)
                self.gather[(xx, yy)] = random.choice(gathers)

        self.generated = True
        return self

    def _fallback_biome(self):
        ids = [b.content_id for b in REGISTRY.all_of("biome")]
        return ids[0] if ids else "noel_village"

    def _tile_walkable(self, tile):
        return tile not in _BLOCKED_TILES

    def decor_blocks(self, lx, ly):
        d = self.decor.get((lx, ly))
        return bool(d and d in self._blocked_decor)

    def tile_at(self, wx, wy, z=0):
        lx, ly = self.local(wx, wy)
        if 0 <= lx < self.size and 0 <= ly < self.size and z in self.tiles:
            return self.tiles[z][ly][lx]
        return None

    def set_tile(self, wx, wy, tile, z=0):
        lx, ly = self.local(wx, wy)
        self.ensure_generated()
        if z not in self.tiles:
            self.tiles[z] = [[None] * self.size for _ in range(self.size)]
        self.tiles[z][ly][lx] = tile

    # ------- 序列化（按区块存储 -> MC 式区块存档） -------
    def to_json(self):
        return {
            "cx": self.cx, "cy": self.cy, "cz": self.cz,
            "biome": self.biome,
            "tiles": [grid for grid in self.tiles.values()] if self.tiles else [],
            "decor": [{"x": k[0], "y": k[1], "v": v} for k, v in self.decor.items()],
            "gather": [{"x": k[0], "y": k[1], "v": v} for k, v in self.gather.items()],
        }

    @classmethod
    def from_json(cls, data):
        c = cls(data["cx"], data["cy"], data.get("cz", 0))
        c.biome = data.get("biome")
        grids = data.get("tiles") or []
        c.tiles = dict(enumerate(grids)) if grids else None
        c.decor = {(d["x"], d["y"]): d["v"] for d in data.get("decor", [])}
        c.gather = {(d["x"], d["y"]): d["v"] for d in data.get("gather", [])}
        biome = REGISTRY.get("biome", c.biome) or {}
        c._blocked_decor = set(biome.get("blocked_decor") or config.BLOCKING_DECOR)
        c.generated = True
        return c


class World:
    """管理所有区块；提供全局坐标查询与落/存。"""

    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 2**31)
        self.chunks = {}
        self.entities = []
        self.player = None
        self._biome_ids = None

    # ------------------------------------------------------------------
    # 地形（确定性噪声，按世界坐标查询，跨区块一致）
    # ------------------------------------------------------------------
    def biome_ids(self):
        if self._biome_ids is None:
            ids = [b.content_id for b in REGISTRY.all_of("biome")]
            self._biome_ids = ids if ids else ["noel_village"]
        return self._biome_ids

    def in_bounds(self, wx, wy):
        if config.WORLD_RADIUS is None:
            return True
        r = config.WORLD_RADIUS
        return max(abs(int(wx)), abs(int(wy))) <= r

    def biome_at(self, wx, wy):
        ids = self.biome_ids()
        if config.SPAWN_PROTECT_RADIUS is not None and wx * wx + wy * wy < \
                config.SPAWN_PROTECT_RADIUS ** 2:
            return "noel_village" if "noel_village" in ids else ids[0]
        n = noise.fbm(wx * config.BIOME_SCALE, wy * config.BIOME_SCALE, self.seed, octaves=2)
        return ids[min(len(ids) - 1, int(n * len(ids)))]

    def height_at(self, wx, wy):
        h = noise.fbm(wx * config.HEIGHT_SCALE, wy * config.HEIGHT_SCALE,
                      self.seed + 101, octaves=5)
        # 重塑：均值抬到 0.48、对比度压到 0.70 -> 陆地占绝大多数，
        # 水/山只在噪声极值处出现，不再满图撞墙。
        h = config.LAND_BIAS + (h - 0.5) * config.LAND_AMP
        if config.SPAWN_PROTECT_RADIUS is not None:
            pr = config.SPAWN_PROTECT_RADIUS
            r = math.hypot(wx, wy)
            # 出生圈外 1.5 倍半径内平滑过渡为陆地，出村先是一大片可探索草甸，
            # 不会“村口一出去就撞水面”。
            if r < pr * 1.5:
                t = max(0.0, 1.0 - r / (pr * 1.5))
                h = h * (1.0 - 0.85 * t) + 0.50 * t
        return h

    def _weighted_variant(self, wx, wy, variants, default):
        total = sum(v.get("weight", 1) for v in variants)
        r = noise.value_noise(wx * 3.1, wy * 3.1, self.seed + 31337) * total
        for v in variants:
            r -= v.get("weight", 1)
            if r <= 0:
                return v.get("tile", default)
        return variants[-1].get("tile", default)

    def tile_for(self, wx, wy):
        """世界坐标 -> tile id（确定性的完整地形判定，跨区块一致）。"""
        if not self.in_bounds(wx, wy):
            return "water_deep"
        if config.SPAWN_PROTECT_RADIUS is not None:
            pr = config.SPAWN_PROTECT_RADIUS
            if wx * wx + wy * wy <= pr * pr:
                return "grass"
        h = self.height_at(wx, wy)
        if h < config.H_DEEP_WATER:
            return "water_deep"
        if h < config.H_SHALLOW:
            return "water"
        if h > config.H_MOUNTAIN:
            return "mountain"
        me = self.biome_at(wx, wy)
        biome = REGISTRY.get("biome", me) or {}
        # 群系过渡带：与四邻主群系不同 -> 泥土带，避免贴图硬切
        if (self.biome_at(wx - 1, wy) != me or self.biome_at(wx + 1, wy) != me or
                self.biome_at(wx, wy - 1) != me or self.biome_at(wx, wy + 1) != me):
            return "dirt"
        base = biome.get("tile", "grass")
        variants = biome.get("tile_variants")
        if variants:
            return self._weighted_variant(wx, wy, variants, base)
        return base

    # ------------------------------------------------------------------
    # 区块访问
    # ------------------------------------------------------------------
    def chunk_coords(self, wx, wy, z=0):
        return int(wx) // CHUNK_SIZE, int(wy) // CHUNK_SIZE, z

    def get_chunk(self, wx, wy, z=0, generate=True):
        key = self.chunk_coords(wx, wy, z)
        c = self.chunks.get(key)
        if c is None and generate:
            c = Chunk(*key)
            c.ensure_generated(self)
            self.chunks[key] = c
        return c

    def tile_at(self, wx, wy, z=0):
        if not self.in_bounds(wx, wy):
            return "water_deep"
        c = self.get_chunk(wx, wy, z)
        return c.tile_at(wx, wy, z)

    def is_walkable(self, wx, wy, z=0):
        if not self.in_bounds(wx, wy):
            return False
        tile = self.tile_at(wx, wy, z)
        if tile in _BLOCKED_TILES:
            return False
        c = self.get_chunk(wx, wy, z)
        lx, ly = c.local(int(wx), int(wy))
        if c.decor_blocks(lx, ly):
            return False
        return True

    # ------------------------------------------------------------------
    # 迭代渲染范围
    # ------------------------------------------------------------------
    def visible_chunks(self, center_wx, center_wy, radius=2, z=0):
        ccx, ccy, _ = self.chunk_coords(center_wx, center_wy, z)
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                yield self.get_chunk((ccx + dx) * CHUNK_SIZE, (ccy + dy) * CHUNK_SIZE, z)

    # ------------------------------------------------------------------
    # 存档：按区块序列化（MC 式区块存储）
    # ------------------------------------------------------------------
    def to_json(self):
        return {
            "seed": self.seed,
            "chunks": [c.to_json() for c in self.chunks.values()],
            "player_pos": [self.player.x, self.player.y] if self.player else None,
        }

    @classmethod
    def from_json(cls, data):
        w = cls(data.get("seed"))
        for cj in data.get("chunks", []):
            c = Chunk.from_json(cj)
            c._seed = w.seed
            w.chunks[(c.cx, c.cy, c.cz)] = c
        return w