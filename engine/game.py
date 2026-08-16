# -*- coding: utf-8 -*-
"""Game 主控：窗口、状态机、主循环、输入、世界模拟与渲染装配。
状态机 (self.mode):
    title    - 标题菜单
    classsel - 新游戏选职业
    savesel  - 存档选择
    playing  - 游戏进行中（含暂停、背包、对话子状态）

自 pyglet 迁移至 arcade：
- GameWindow 继承 arcade.Window，on_draw/on_update/键盘鼠标事件统一在此转发给 Game；
- 按键状态用 self.keys(set) 在按下/释放时维护，替代 pyglet KeyStateHandler；
- 绘制批处理使用 draw_util.Batch（内部封装 arcade ShapeElementList + Text）；
- 静态地形使用 arcade.SpriteList.draw(pixelated=True) 开启最近邻滤镜。
"""
import math
import random
import arcade
from arcade import key

from . import config
from . import render as R
from .camera import Camera
from .world import World
from .player import Player
from .enemy import Enemy
from .npc import NPC
from .item_entity import GroundItem
from .projectile import Projectile
from .combat import CombatSystem, ParticlePool
from .crafting import GatherSystem, Cauldron, Forge
from .quests import QuestManager
from .save import SaveManager
from .vector2 import Vec2
from .registry import REGISTRY
from .ui.draw_util import (
    add_rect, add_text, add_border, add_circle,
    set_viewport_h, begin_frame, Batch,
)
from .ui.hud import HUD
from .ui.inventory_screen import InventoryScreen
from .ui.dialog import DialogBox
from .ui.menus import TitleMenu, ClassSelectMenu, SaveScreen, PauseMenu
from .terrain import TerrainCache

# 区块边长（与 world.CHUNK_SIZE 保持一致，避免与 config 耦合）
_CHUNK = 16


class GameWindow(arcade.Window):
    """arcade 窗口子类：负责事件循环与渲染/更新入口，全部转发给 Game。"""

    def __init__(self, game):
        super().__init__(
            config.Graphics.WINDOW_W,
            config.Graphics.WINDOW_H,
            config.Graphics.TITLE,
            resizable=config.Graphics.RESIZABLE,
            vsync=config.Graphics.VSYNC,
        )
        if config.Graphics.RESIZABLE:
            self.set_minimum_size(800, 480)
        # 替代 pyglet.clock.schedule_interval
        self.set_update_rate(1.0 / config.Graphics.FPS)
        self.game = game
        # 替代 pyglet shapes.Rectangle 垫底色：clear() 时自动填充
        self.background_color = (58, 108, 168)

    def on_draw(self):
        self.clear()
        self.game.render()

    def on_update(self, dt):
        self.game.update(dt)

    def on_key_press(self, symbol, modifiers):
        self.game.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.game.on_key_release(symbol, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self.game.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self.game.on_mouse_press(x, y, button, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.game.on_mouse_scroll(x, y, scroll_x, scroll_y)


class Game:
    """游戏主控制器。窗口为 GameWindow（arcade.Window 子类），持有于 self.window。"""

    def __init__(self):
        config.init_dirs()
        config.load_settings_from_json()
        self.mode = "title"
        self.world = None
        self.player = None
        self.camera = Camera()
        self.combat = CombatSystem(self)
        self.particles = ParticlePool()
        self.gather = None
        self.quest_mgr = None
        self.save_manager = SaveManager()

        # 子界面
        self.hud = HUD(self)
        self.inventory_screen = InventoryScreen(self)
        self.dialog = DialogBox()
        self.menus = {
            "title": TitleMenu(self),
            "classsel": ClassSelectMenu(self),
            "savesel": SaveScreen(self),
            "pause": PauseMenu(self),
        }
        self.current_menu = self.menus["title"]

        # 输入状态：用 set 维护按下的键（替代 pyglet KeyStateHandler）
        self.keys = set()
        self._mouse = (0, 0)
        self._ui = "none"  # 'inventory' | 'dialog' | None

        # ★ 关键：先创建窗口！
        # arcade 3.x 的 ShapeElementList / Sprite / SpriteList 在构造时需要
        # 活动窗口的 OpenGL 上下文，所以窗口必须先于所有绘制对象创建。
        self.window = GameWindow(self)

        # 批处理（依赖窗口上下文，必须在窗口创建之后）
        self.batch = Batch()
        self.world_batch = Batch()
        self.ui_batch = Batch()

        # 静态地形层：每个区块烘焙成一张贴图并缓存（饥荒式精细地面 + 高性能）。
        self.terrain = TerrainCache(capacity=96)
        self.terrain_list = arcade.SpriteList()
        self._warm_chunks = set()  # 已预热的区块

        self.current_slot = 1
        self._populate_spawn = True

    # --- 窗口尺寸透传（供 UI 模块通过 self.game.width/height 读取） ---
    @property
    def width(self):
        return self.window.width

    @property
    def height(self):
        return self.window.height

    def run(self):
        arcade.run()

    # ------------------------------------------------------------------
    # 状态切换
    # ------------------------------------------------------------------
    def switch_class(self):
        self.mode = "classsel"
        self.current_menu = ClassSelectMenu(self)

    def switch_title(self):
        self.mode = "title"
        self.current_menu = TitleMenu(self)

    def open_save_screen(self):
        self.mode = "savesel"
        self.current_menu = SaveScreen(self)

    def new_game(self, klass_id):
        config.init_dirs()
        self.world = World(seed=random.randint(0, 2**31))
        self._warm_chunks.clear()
        self.terrain.clear()
        self.player = Player(8.0, 8.0)
        self.player.klass = klass_id
        self.player.auto_level_base_stats()
        self.player.auto_learn_skills()
        self.player.recalc_stats()
        self.world.player = self.player
        self._setup_world()
        self.start_playing()

    def load_slot(self, slot):
        data = self.save_manager.load(slot)
        if data is None:
            # 空档 -> 当作新游戏
            return self.new_game("swordsman")
        self.current_slot = slot
        self.world = World.from_json(data["world"])
        self.player = Player.from_json(data["player"])
        self.world.player = self.player
        self._setup_world(spawn_pets=False)
        self.start_playing()
        self.player.x, self.player.y = data["player"].get("x", 8), data["player"].get("y", 8)

    def _setup_world(self, spawn_pets=True):
        if self.player is None:
            return
        self.world.entities = []

        # NPC（城镇与村庄）
        for npc_base in REGISTRY.all_of("npc"):
            if npc_base.get("town") in ("frantia", "noel_village"):
                nx = self.player.x + random.uniform(-3, 3)
                ny = self.player.y + random.uniform(-5, 5)
                if spawn_pets:
                    n = NPC(npc_base.content_id, nx, ny)
                    self.world.entities.append(n)

        # 初始几只野猪
        if spawn_pets:
            for _ in range(4):
                ex = self.player.x + random.uniform(-6, 6)
                ey = self.player.y + random.uniform(-6, 6)
                e = Enemy("wild_boar", ex, ey)
                e.on_death_cb = self.on_enemy_death
                self.world.entities.append(e)

        self.quest_mgr = QuestManager(self.player)
        self.quest_mgr.load_progress(self.player.quests)
        self.gather = GatherSystem(self.player)

    def start_playing(self):
        self.mode = "playing"
        self._ui = "none"
        self.camera.attach(self.player)

    def resume(self):
        self.mode = "playing"
        self._ui = "none"

    def quick_save(self):
        self.save_to_slot(self.current_slot)

    def save_to_slot(self, slot):
        self.current_slot = slot
        self.save_manager.save(slot, f"元素之诗 - 存档 {slot}", self)

    def save_and_menu(self):
        self.save_to_slot(self.current_slot)
        self.switch_title()

    def quit(self):
        arcade.close_window()

    def pause(self):
        if self.mode == "playing" and self._ui == "none":
            self.mode = "pause"
            self._ui = "pause"

    # ------------------------------------------------------------------
    # 序列化
    # ------------------------------------------------------------------
    def player_to_json(self):
        return self.player.to_json()

    # ------------------------------------------------------------------
    # 世界模拟 / 更新
    # ------------------------------------------------------------------
    def update(self, dt):
        if self.mode != "playing":
            return
        if self._ui in ("inventory", "pause"):
            return

        p = self.player

        # 移动
        move_x = (key.RIGHT in self.keys or key.D in self.keys) - \
                 (key.LEFT in self.keys or key.A in self.keys)
        move_y = (key.UP in self.keys or key.W in self.keys) - \
                 (key.DOWN in self.keys or key.S in self.keys)
        if move_x:
            p.facing = 1 if move_x > 0 else -1
        d = math.hypot(move_x, move_y) or 1
        if self._ui == "none" and not p.is_stunned():
            p.move(move_x / d * p.speed * dt, move_y / d * p.speed * dt, self.world, dt)
        p.regen_resource(dt)

        # 敌人 AI 与更新
        for e in self.world.entities:
            if isinstance(e, Enemy):
                e.update_ai(dt, p, self.world)
            elif isinstance(e, (GroundItem, NPC)):
                e.update(dt, self.world)
        self.world.entities[:] = [e for e in self.world.entities if e.alive]

        # 投射物
        for pr in [x for x in self.world.entities if isinstance(x, Projectile)]:
            if not pr.alive:
                continue
            cont = pr.update(dt, self.world)
            for target in self._hostile_targets(pr):
                pr.try_hit(target)
            if not cont:
                pr.alive = False
        self.world.entities[:] = [e for e in self.world.entities if e.alive]

        # 拾取物品
        for g in [e for e in self.world.entities if isinstance(e, GroundItem) and e.alive]:
            if g.pos.dist(p.pos) < 1.0:
                p.inventory.add(g.item_id, g.count)
                g.alive = False
        self.world.entities[:] = [e for e in self.world.entities if e.alive]

        self.particles.update(dt)
        self._warm_terrain()
        self.camera.update(dt)

    # ------------------------------------------------------------------
    # 目标筛选
    # ------------------------------------------------------------------
    def _hostile_targets(self, projectile):
        p = projectile
        for e in self.world.entities:
            if e is p.owner:
                continue
            if isinstance(e, Enemy):
                yield e
            elif isinstance(e, Player) and p.is_friendly is False:
                yield e

    def apply_aoe(self, cx, cy, radius, damage, iface=None, skill=None):
        for e in self.world.entities:
            if e is iface or not getattr(e, "alive", True):
                continue
            if isinstance(e, Enemy):
                if Vec2(e.x, e.y).dist(Vec2(cx, cy)) <= radius:
                    e.take_damage(damage, iface)
            elif isinstance(e, Player) and e is not iface and e.klass:
                pass

    def spawn_projectile(self, projectile):
        self.world.entities.append(projectile)

    def get_allies(self, player):
        return [player]

    # ------------------------------------------------------------------
    # 敌人死亡回调
    # ------------------------------------------------------------------
    def on_enemy_death(self, enemy):
        p = self.player
        if p is None:
            return
        p.add_exp(enemy.exp_reward)

        # 掉落
        for it_id, cnt in getattr(enemy, "loot", []):
            g = GroundItem(it_id, enemy.x + random.uniform(-0.5, 0.5),
                           enemy.y + random.uniform(-0.5, 0.5), cnt)
            self.world.entities.append(g)

        # 任务记录
        if self.quest_mgr:
            self.quest_mgr.record_quests("kill", enemy.monster_id)

    # ------------------------------------------------------------------
    # 交互
    # ------------------------------------------------------------------
    def interact(self):
        p = self.player
        if p is None:
            return
        for e in self.world.entities:
            if getattr(e, "interactable", False) and e.pos.dist(p.pos) <= e.interact_range:
                if isinstance(e, NPC):
                    self.dialog.show(e)
                    self._ui = "dialog"
                    return
                if isinstance(e, GroundItem):
                    pass

    # ------------------------------------------------------------------
    # 开背包
    # ------------------------------------------------------------------
    def toggle_inventory(self):
        if self._ui == "inventory":
            self._ui = "none"
        elif self._ui == "none":
            self._ui = "inventory"

    # ------------------------------------------------------------------
    # 技能施放（玩家按键）
    # ------------------------------------------------------------------
    def cast_skill_index(self, idx):
        p = self.player
        if p is None or self._ui != "none":
            return
        if idx >= len(p.skills_learned):
            return
        sid = p.skills_learned[idx]
        # 朝向目标方向
        tx, ty = self.camera.screen_to_world(*self._mouse)
        dx = tx - p.x
        dy = ty - p.y
        dl = math.hypot(dx, dy) or 1
        self.combat.cast_skill(p, sid, dx / dl, dy / dl)

    # ------------------------------------------------------------------
    # 喝药
    # ------------------------------------------------------------------
    def use_potion(self):
        p = self.player
        if p is None:
            return
        for stack in p.inventory.slots:
            if stack and stack.base.get("use") in ("heal", "mana", "food"):
                kind = stack.base.get("use")
                if kind == "heal":
                    p.heal(stack.base.get("heal", 100))
                elif kind == "mana":
                    p.resource = min(p.max_resource, p.resource + stack.base.get("mana", 30))
                p.inventory.remove(stack.item_id, 1)
                return

    # ==================================================================
    # 渲染
    # ==================================================================
    def render(self):
        # 窗口背景已由 GameWindow.on_draw 的 self.clear() 填充（背景色见 GameWindow）。
        # 统一整个项目使用「左上原点、Y 向下」坐标（见 config 注释）；
        # draw_util 会据此把 shapes/Text 翻转到 arcade 的左下原点坐标。
        set_viewport_h(self.height)
        # 每帧重建 ui_batch / world_batch，避免对象无限累积导致残留与卡顿。
        begin_frame()
        self.ui_batch = Batch()
        if self.mode == "playing":
            self._draw_world()
            self._draw_hud()
        else:
            if self.current_menu:
                self.current_menu.draw(self.ui_batch)
            self.ui_batch.draw()

    def _draw_world(self):
        # 动态层（装饰/采集/实体/玩家/粒子）用每帧新 batch，避免累积
        self.world_batch = Batch()
        p = self.player
        if not self.world or not p:
            return

        # 1) 静态地面层（区块贴图，性能核心，先画保证在下层）
        self._draw_terrain_textures()
        # 2) 动态层
        self._draw_decor_layer()
        self._draw_gather()
        for e in sorted(self.world.entities, key=lambda e: e.y):
            self._draw_entity(e)
        self._draw_player()
        self._draw_particles()
        self.world_batch.draw()

    def _draw_decor_layer(self):
        """绘制可见区块的装饰物（世界固定物）。"""
        p = self.player
        if not p or not self.world:
            return
        W = self.width
        H = self.height
        CS = _CHUNK
        ccx, ccy, _ = self.world.chunk_coords(p.x, p.y)
        for cx in range(ccx - 2, ccx + 3):
            for cy in range(ccy - 2, ccy + 3):
                chunk = self.world.get_chunk(cx * CS, cy * CS)
                if not chunk.decor:
                    continue
                ox, oy = chunk.world_origin()
                for (lx, ly), decor in chunk.decor.items():
                    x = ox + lx
                    y = oy + ly
                    sx, sy = self.camera.world_to_screen(x + 0.5, y + 0.5)
                    if sx < -48 or sy < -48 or sx > W + 48 or sy > H + 48:
                        continue
                    self._draw_decor(sx, sy, decor)

    def _draw_decor(self, sx, sy, decor):
        """用少量几何组合出「饥荒式」树木/灌木/岩石（量少，成本低）。"""
        if decor == "tree":
            add_rect(self.world_batch, sx - 2, sy - 6, 4, 10, (110, 75, 45))
            add_circle(self.world_batch, sx, sy + 2, 9, (50, 105, 45))
            add_circle(self.world_batch, sx - 4, sy + 1, 5, (60, 120, 52))
            add_circle(self.world_batch, sx + 4, sy + 1, 5, (60, 120, 52))
        elif decor == "pine":
            add_rect(self.world_batch, sx - 2, sy - 6, 4, 9, (95, 65, 40))
            add_circle(self.world_batch, sx, sy + 3, 7, (35, 80, 55))
            add_circle(self.world_batch, sx, sy + 7, 5, (35, 90, 58))
        elif decor == "bush":
            add_circle(self.world_batch, sx, sy, 5, (60, 125, 55))
            add_circle(self.world_batch, sx - 3, sy - 1, 3, (70, 140, 62))
        elif decor == "rock":
            add_rect(self.world_batch, sx - 6, sy - 8, 12, 7, (150, 150, 150))
            add_rect(self.world_batch, sx - 3, sy - 5, 7, 4, (130, 130, 132))
        elif decor == "snow_rock":
            add_rect(self.world_batch, sx - 6, sy - 8, 12, 7, (205, 215, 225))
            add_rect(self.world_batch, sx - 3, sy - 5, 7, 4, (180, 192, 205))
        elif decor == "flower":
            add_rect(self.world_batch, sx - 1, sy - 3, 2, 4, (70, 120, 50))
            add_circle(self.world_batch, sx, sy + 1, 3, (225, 120, 185))
        elif decor == "crystal":
            add_rect(self.world_batch, sx - 4, sy - 8, 8, 8, (150, 200, 255))
            add_rect(self.world_batch, sx - 2, sy - 4, 4, 4, (200, 230, 255))
        elif decor == "dead_tree":
            add_rect(self.world_batch, sx - 2, sy - 8, 4, 10, (90, 65, 50))
            add_rect(self.world_batch, sx - 5, sy - 4, 4, 3, (90, 65, 50))
        elif decor == "cave":
            add_circle(self.world_batch, sx, sy, 6, (45, 45, 45))
            add_circle(self.world_batch, sx, sy + 2, 4, (25, 25, 25))
        elif decor == "slime_pool":
            add_circle(self.world_batch, sx, sy, 6, (95, 160, 105))
            add_circle(self.world_batch, sx - 2, sy - 1, 3, (70, 140, 80))
        else:
            add_rect(self.world_batch, sx - 6, sy - 6, 12, 12, (120, 120, 120))

    def _draw_gather(self):
        p = self.player
        if not p or not self.world:
            return
        W = self.width
        H = self.height
        ccx, ccy, _ = self.world.chunk_coords(p.x, p.y)
        for cx in range(ccx - 2, ccx + 3):
            for cy in range(ccy - 2, ccy + 3):
                chunk = self.world.get_chunk(cx * 16, cy * 16)
                if not chunk.gather:
                    continue
                ox, oy = chunk.world_origin()
                for (lx, ly), gid in list(chunk.gather.items()):
                    wx = ox + lx + 0.5
                    wy = oy + ly + 0.5
                    sx, sy = self.camera.world_to_screen(wx, wy)
                    if sx < -32 or sy < -32 or sx > W + 32 or sy > H + 32:
                        continue
                    g = REGISTRY.get("gather", gid)
                    icon = g.get("icon", "log") if g else "log"
                    color = R.IconCache().color_of(icon)
                    add_rect(self.world_batch, sx - 6, sy - 14, 12, 12, color)
                    add_text(self.world_batch, g.get("name", "?") if g else "?",
                             sx, sy + 14, size=8, color=(235, 235, 235))

    def _draw_entity(self, e):
        sx, sy = self.camera.world_to_screen(e.x, e.y)
        if isinstance(e, Enemy):
            add_rect(self.world_batch, sx - 12, sy - 18, 24, 24,
                     (210 if e.boss else 170, 40, 40))
            # 血条
            self._draw_entity_bar(sx - 15, sy + 10, 30, 3, e.hp / e.max_hp, (200, 40, 40))
            # 名字
            if e.boss:
                add_text(self.world_batch, e.name(), sx, sy + 16, size=9,
                         color=(255, 220, 100))
        elif isinstance(e, NPC):
            add_rect(self.world_batch, sx - 11, sy - 16, 22, 22, (90, 160, 230))
            add_text(self.world_batch, e.name, sx, sy + 14, size=9,
                     color=(230, 230, 230))
        elif isinstance(e, GroundItem):
            color = R.IconCache().color_of(e.icon)
            add_rect(self.world_batch, sx - 5, sy - 14, 10, 10, color)
        elif isinstance(e, Projectile):
            pcol = {"fireball": (255, 120, 40),
                    "ice_spear": (120, 190, 255),
                    "arrow": (220, 190, 120),
                    "pierce_arrow": (200, 220, 255)}.get(e.kind, (230, 230, 230))
            add_circle(self.world_batch, sx, sy, 5, pcol)

    def _draw_entity_bar(self, sx, sy, w, h, pct, color):
        add_rect(self.world_batch, sx, sy, w, h, (30, 30, 30))
        add_rect(self.world_batch, sx, sy, int(w * pct), h, color)

    def _draw_player(self):
        p = self.player
        sx, sy = self.camera.world_to_screen(p.x, p.y)
        color = {"swordsman": (220, 190, 120),
                 "knight": (150, 180, 230),
                 "mage": (200, 130, 220),
                 "ranger": (130, 220, 150)}.get(p.klass, (200, 200, 200))
        add_rect(self.world_batch, sx - 9, sy - 18, 18, 22, color)
        # 朝向指示
        if p.facing > 0:
            add_rect(self.world_batch, sx + 9, sy - 6, 5, 4, (40, 40, 40))
        else:
            add_rect(self.world_batch, sx - 14, sy - 6, 5, 4, (40, 40, 40))
        # 受击闪红
        if p.hit_timer > 0:
            add_rect(self.world_batch, sx - 9, sy - 18, 18, 22, (255, 60, 60, 160))

    def _draw_particles(self):
        for pa in self.particles.particles:
            sx, sy = self.camera.world_to_screen(pa["x"], pa["y"])
            a = int(255 * (pa["life"] / pa["max"]))
            add_circle(self.world_batch, sx, sy, pa["size"] * 3, (*pa["color"], a))

    def _draw_terrain_textures(self):
        """绘制可见区块的静态地面贴图（每帧重摆位 + NEAREST + 绘制）。

        自 pyglet 迁移：
        - 不再手动 glTexParameteri 强制 NEAREST，改用 SpriteList.draw(pixelated=True)；
        - arcade 3.x 的 Sprite 以「中心」定位，由原 pyglet 的左下角公式 + 精灵宽高换算中心。
        """
        p = self.player
        if not self.world or not p:
            return
        T = config.TILE
        W = self.width
        H = self.height
        cam = self.camera

        self.terrain_list.clear()
        ccx, ccy, _ = self.world.chunk_coords(p.x, p.y)
        for cx in range(ccx - 2, ccx + 3):
            for cy in range(ccy - 2, ccy + 3):
                chunk = self.world.get_chunk(cx * _CHUNK, cy * _CHUNK)
                if not chunk.tiles:
                    continue
                tex, sprite = self.terrain.get(chunk, self.world)
                # 原 pyglet 版本 sprite.x/y 是「左下角」；arcade 需要「中心点」
                left = round((chunk.cx * _CHUNK - cam.pos.x) * T + W / 2)
                bottom = round(H / 2 + (chunk.cy * _CHUNK - cam.pos.y) * T)
                sprite.center_x = left + sprite.width / 2
                sprite.center_y = bottom + sprite.height / 2
                self.terrain_list.append(sprite)
        self.terrain_list.draw(pixelated=True)

    def _draw_hud(self):
        # 背景交互提示
        p = self.player
        nearby = [e for e in self.world.entities
                  if getattr(e, "interactable", False) and e.pos.dist(p.pos) <= 2.2]
        if nearby and self._ui == "none":
            e = nearby[0]
            if isinstance(e, NPC):
                sx, sy = self.camera.world_to_screen(p.x, p.y - 1)
                add_text(self.ui_batch, "[E] 与 " + e.name + " 交谈",
                         sx, sy - 34, size=11, color=(255, 255, 120))

        # 其它 UI
        if self._ui == "none":
            self.hud.draw(self.ui_batch)
        elif self._ui == "inventory":
            self.inventory_screen.draw(self.ui_batch)
        elif self._ui == "dialog":
            self.dialog.draw(self.ui_batch, self.width, self.height)

        # 准星
        if self._ui == "none" and self.mode == "playing":
            add_circle(self.ui_batch, self._mouse[0], self._mouse[1], 3,
                       (250, 250, 250, 220))

    def _warm_terrain(self):
        """提前生成/烘焙玩家周围的区块（半径 3 > 可见半径 2），摊到多帧。"""
        p = self.player
        if not self.world or not p:
            return
        ccx, ccy, _ = self.world.chunk_coords(p.x, p.y)
        gen_budget = 10
        bake_budget = 2
        for cx in range(ccx - 3, ccx + 4):
            for cy in range(ccy - 3, ccy + 4):
                k = (cx, cy)
                if k in self._warm_chunks:
                    continue
                chunk = self.world.get_chunk(cx * _CHUNK, cy * _CHUNK, 0, generate=False)
                if chunk is None:
                    if gen_budget <= 0:
                        continue
                    chunk = self.world.get_chunk(cx * _CHUNK, cy * _CHUNK)
                    gen_budget -= 1
                if chunk.tiles:
                    if bake_budget <= 0:
                        continue
                    self.terrain.get(chunk, self.world)
                    bake_budget -= 1
                self._warm_chunks.add(k)

    # ==================================================================
    # 输入处理
    # ==================================================================
    def on_key_press(self, symbol, modifiers):
        config.load_settings_from_json()
        self.keys.add(symbol)

        if self.mode != "playing":
            # 菜单导航（回车确认首个按钮即可 / ESC 返回）
            if symbol == key.ENTER or symbol == key.SPACE:
                if self.current_menu and self.current_menu.buttons:
                    # 直接触发第一个按钮（简单交互）
                    self.current_menu.click(
                        self.current_menu.buttons[0].x + 1,
                        self.current_menu.buttons[0].y + 1)
            if symbol == key.ESCAPE:
                if self.mode in ("classsel", "savesel"):
                    self.switch_title()
            return

        # playing
        p = self.player

        if symbol == key.ESCAPE:
            if self._ui == "none":
                self.pause()
            elif self._ui == "inventory":
                self._ui = "none"
            elif self._ui == "dialog":
                self._ui = "none"
            return

        if symbol == key.B or symbol == key.C:
            self.toggle_inventory()
            return

        if symbol == key.E:
            if self._ui == "dialog":
                self._ui = "none"
            else:
                self.interact()
            return

        if symbol == key.Q and self._ui == "inventory":
            self._equip_or_unequip()
            return

        if symbol == key.KEY_1:
            self.use_potion()
            return

        # 技能键
        skill_keys = {key.J: 0, key.K: 1, key.U: 2, key.I: 3, key.O: 4}
        if symbol in skill_keys:
            self.cast_skill_index(skill_keys[symbol])

        # 空格：翻滚/招架
        if symbol == key.SPACE:
            self._dash_or_block()

    def on_key_release(self, symbol, modifiers):
        """释放按键：从 self.keys 中移除（替代 pyglet KeyStateHandler）。"""
        self.keys.discard(symbol)

    def _equip_or_unequip(self):
        p = self.player
        # 找到第一个可装备物品
        for i, stack in enumerate(p.inventory.slots):
            if stack and stack.is_equipment:
                slot = stack.base.get("slot")
                # 穿戴
                if p.equipment.get(slot) is None:
                    p.equipment[slot] = stack
                    p.inventory.slots[i] = None
                    p.recalc_stats()
                    return
                else:
                    # 交换
                    old = p.equipment[slot]
                    p.equipment[slot] = stack
                    p.inventory.slots[i] = old
                    p.recalc_stats()
                    return

    def _dash_or_block(self):
        p = self.player
        if p is None:
            return
        # 简化为小翻滚（赋予短暂位移），不占用太多
        step = p.facing * 2.0
        p.move(step * 0.05, 0, self.world, 1)

    def on_mouse_motion(self, x, y, dx, dy):
        # arcade 鼠标 y 是左下原点向上；统一转换为项目「左上 Y 向下」坐标
        y = self.height - y
        self._mouse = (x, y)
        if self.mode != "playing" and self.current_menu:
            self.current_menu.motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        # arcade 鼠标 y 是左下原点向上；统一转换为项目「左上 Y 向下」坐标
        y = self.height - y
        if self.mode != "playing" and self.current_menu:
            self.current_menu.click(x, y)
        elif self.mode == "playing":
            self._mouse = (x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass
