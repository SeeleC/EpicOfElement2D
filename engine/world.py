# -*- coding: utf-8 -*-
"""世界 / 地图 / 区块 (World / Chunk)。

对应「存档模式类似于 Minecraft」的核心设计：
    - 世界按固定大小的「区块 (Chunk)」划分，例如 16x16 格子。
    - 每个区块记录方块/地面类型、装饰物、采集物、实体初始点等。
    - 区块按需生成，并可按区块单独序列化进 JSON 存档。
    - 只有被玩家访问过的区块才会被持久化保存（懒加载 + 按区块存储）。

这样实现了 MC 式的「区块数据持久化」与无限/大世界扩展。
"""
import random

from . import config
from .registry import REGISTRY


CHUNK_SIZE = 16            # 区块边长（格子数）
MAX_LEVEL = 4              # 最大分层（世界高度，类似 Y 轴层数）


class Chunk:
    """单个区块。保存该区块内所有格子与逻辑实体引用。"""

    def __init__(self, cx, cy, cz=0):
        self.cx = cx          # 区块世界坐标
        self.cy = cy
        self.cz = cz
        self.size = CHUNK_SIZE
        # tiles[z][y][x] -> tile_id (字符串，如 'grass')，用于渲染地面
        self.tiles = None     # 惰性生成
        # decor[(x,y)] -> decor_id 装饰物
        self.decor = {}
        # gather[(x,y)] -> gather_id 采集物（尚未采完）
        self.gather = {}
        self.generated = False

    # ------- 坐标换算 -------
    def abs_size(self):
        return CHUNK_SIZE

    def world_origin(self):
        """区块左上角的世界格子坐标。"""
        return self.cx * CHUNK_SIZE, self.cy * CHUNK_SIZE

    def local(self, wx, wy):
        ox, oy = self.world_origin()
        return wx - ox, wy - oy

    def ensure_generated(self):
        if not self.generated:
            self.generate()
        return self

    def generate(self):
        """按生物群系程序化生成地面(tile)与装饰。"""
        ox, oy = self.world_origin()
        biome_id = self._pick_biome()
        biome = REGISTRY.get("biome", biome_id) or {}

        self.tiles = {}
        for z in range(1):
            grid = []
            for yy in range(self.size):
                row = []
                for xx in range(self.size):
                    wx, wy = ox + xx, oy + yy
                    row.append(self._tile_for(biome, wx, wy))
                grid.append(row)
            self.tiles[z] = grid
        self.biome = biome_id

        # 装饰物
        decors = biome.get("decor") or ["tree", "bush"]
        for yy in range(self.size):
            for xx in range(self.size):
                if random.random() < 0.06:
                    tile = self.tiles[0][yy][xx]
                    if self._tile_walkable(tile):
                        self.decor[(xx, yy)] = random.choice(decors)

        # 采集物
        gathers = biome.get("gather") or []
        if gathers:
            for _ in range(3):
                xx = random.randrange(self.size)
                yy = random.randrange(self.size)
                self.gather[(xx, yy)] = random.choice(gathers)

        self.generated = True
        return self

    def _pick_biome(self):
        """区块的生物群系：使用确定性伪随机（同区块始终一致）。"""
        r = random.Random(self.cx * 31 + self.cy * 17)
        biomes = [b.content_id for b in REGISTRY.all_of("biome")]
        return r.choice(biomes) if biomes else "noel_village"

    def _tile_for(self, biome, wx, wy):
        r = random.Random(wx * 7 + wy * 11)
        base = biome.get("tile", "grass")
        # 简单噪音：偶尔混入变体
        if r.random() < 0.05:
            return "grass"
        return base

    def _tile_walkable(self, tile):
        return tile in ("grass", "snow", "waste")

    def tile_at(self, wx, wy, z=0):
        lx, ly = self.local(wx, wy)
        if 0 <= lx < self.size and 0 <= ly < self.size and z in self.tiles:
            return self.tiles[z][ly][lx]
        return None

    def set_tile(self, wx, wy, tile, z=0):
        lx, ly = self.local(wx, wy)
        self.ensure_generated()
        if z not in self.tiles:
            self.tiles[z] = [[None]*self.size for _ in range(self.size)]
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
        c.generated = True
        return c


class World:
    """管理所有区块；提供全局坐标查询与落/存。"""

    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 2**31)
        self.chunks = {}      # (cx,cy,cz) -> Chunk
        self.entities = []    # 本世界中的所有活跃逻辑实体(玩家/怪物/NPC)
        self.player = None

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
            c.ensure_generated()
            self.chunks[key] = c
        return c

    def tile_at(self, wx, wy, z=0):
        c = self.get_chunk(wx, wy, z)
        return c.tile_at(wx, wy, z)

    def is_walkable(self, wx, wy, z=0):
        tile = self.tile_at(wx, wy, z)
        if tile is None:
            return False
        if tile == "rock" or tile == "mountain":
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
            w.chunks[(c.cx, c.cy, c.cz)] = c
        return w
