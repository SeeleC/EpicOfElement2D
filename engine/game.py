# -*- coding: utf-8 -*-
"""Game 主控：窗口、状态机、主循环、输入、世界模拟与渲染装配。

状态机 (self.mode):
    title    - 标题菜单
    classsel - 新游戏选职业
    savesel  - 存档选择
    playing  - 游戏进行中（含暂停、背包、对话子状态）
"""
import math
import random

import pyglet
from pyglet.window import key

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

from .ui.draw_util import add_rect, add_text, add_border, add_circle
from .ui.hud import HUD
from .ui.inventory_screen import InventoryScreen
from .ui.dialog import DialogBox
from .ui.menus import TitleMenu, ClassSelectMenu, SaveScreen, PauseMenu


class Game:
    """游戏主控制器（非 Window 子类）。

    完全仿照 pyglet_example/version4/asteroid.py 的窗口构建方式：
    - 窗口是普通 pyglet.window.Window 实例（模块化持有于 self.window）；
    - on_draw 由 main.py 用 @window.event 注册，本类只提供 render() 绘制；
    - 事件处理器（键盘/鼠标）由 main.py 通过 window.push_handlers 显式注册。
    """
    def __init__(self):
        config.init_dirs()
        config.load_settings_from_json()
        self.window = pyglet.window.Window(
            config.Graphics.WINDOW_W, config.Graphics.WINDOW_H,
            caption=config.Graphics.TITLE,
            resizable=config.Graphics.RESIZABLE,
            vsync=config.Graphics.VSYNC)
        if config.Graphics.RESIZABLE:
            self.window.set_minimum_size(800, 480)

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

        # 输入状态
        self.keys = pyglet.window.key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        self._mouse = (0, 0)
        self._ui = "none"   # 'inventory' | 'dialog' | None

        self.batch = pyglet.graphics.Batch()
        self.world_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()

        self.current_slot = 1
        self._populate_spawn = True

        # set fps clock
        self.clock = pyglet.clock.get_default()
        pyglet.clock.schedule_interval(self.update, 1 / config.Graphics.FPS)

    # --- 窗口尺寸透传（供 UI 模块通过 self.game.width/height 读取） ---
    @property
    def width(self):
        return self.window.width

    @property
    def height(self):
        return self.window.height


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
        pyglet.app.exit()

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
        move_x = (self.keys[key.RIGHT] or self.keys[key.D]) - (self.keys[key.LEFT] or self.keys[key.A])
        move_y = (self.keys[key.UP] or self.keys[key.W]) - (self.keys[key.DOWN] or self.keys[key.S])
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
        # 窗口已由 main.py 的 @window.event on_draw 负责 clear()，
        # 此处只绘制内容（仿 asteroid.py：on_draw 里 clear + main_batch.draw()）。
        # 注意：draw_util 内部已对所有 shapes/Label 做引用保活（_KEEP），
        # 因此每帧重建 batch 也不会被 GC 导致画不出内容。
        if self.mode == "playing":
            self._draw_world()
            self._draw_hud()
        else:
            self.ui_batch = pyglet.graphics.Batch()
            if self.current_menu:
                self.current_menu.draw(self.ui_batch)
        self.ui_batch.draw()

    def _draw_world(self):
        self.world_batch = pyglet.graphics.Batch()
        p = self.player
        if not self.world or not p:
            return

        # 绘制可视区块地面
        vis_w, vis_h = config.Graphics.visible_tiles()
        ccx, ccy, _ = self.world.chunk_coords(p.x, p.y)
        for cx in range(ccx - 2, ccx + 3):
            for cy in range(ccy - 2, ccy + 3):
                chunk = self.world.get_chunk(cx * 16, cy * 16)
                self._draw_chunk(chunk)

        # 绘制采集物（叠加在地面上）
        self._draw_gather()

        # 绘制实体
        for e in sorted(self.world.entities, key=lambda e: e.y):
            self._draw_entity(e)

        # 玩家
        self._draw_player()

        # 粒子
        self._draw_particles()

        self.world_batch.draw()

    def _draw_chunk(self, chunk):
        ox, oy = chunk.world_origin()
        biome = REGISTRY.get("biome", chunk.biome) or {}
        ground = biome.get("colors", {}).get("ground", (90, 140, 70))
        edge = biome.get("colors", {}).get("edge", (60, 110, 45))
        for z, grid in (chunk.tiles or {}).items():
            for ly, row in enumerate(grid):
                for lx, tile in enumerate(row):
                    x = ox + lx
                    y = oy + ly
                    color = ground if self.world.is_walkable(x, y) else edge
                    sx, sy = self.camera.world_to_screen(x, y)
                    add_rect(self.world_batch, sx, sy, config.TILE, config.TILE, color)
        # 装饰物
        for (lx, ly), decor in chunk.decor.items():
            x = ox + lx
            y = oy + ly
            sx, sy = self.camera.world_to_screen(x + 0.5, y + 0.5)
            self._draw_decor(sx, sy, decor)
        # 采集物标记点已在 _draw_gather 处理

    def _draw_decor(self, sx, sy, decor):
        color = {"tree": (60, 110, 50), "bush": (70, 140, 60), "flower": (220, 120, 180),
                 "rock": (150, 150, 150), "pine": (40, 90, 60), "cave": (60, 60, 60),
                 "dead_tree": (80, 60, 50), "crystal": (150, 200, 255),
                 "snow_rock": (200, 210, 220), "slime_pool": (90, 160, 100)
                 }.get(decor, (120, 120, 120))
        add_rect(self.world_batch, sx-8, sy-8, 16, 16, color)

    def _draw_gather(self):
        p = self.player
        if not p or not self.world:
            return
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
                    g = REGISTRY.get("gather", gid)
                    icon = g.get("icon", "log") if g else "log"
                    color = R.IconCache().color_of(icon)
                    add_rect(self.world_batch, sx-6, sy-14, 12, 12, color)
                    add_text(self.world_batch, g.get("name", "?") if g else "?",
                             sx, sy + 14, size=8, color=(235, 235, 235))

    def _draw_entity(self, e):
        sx, sy = self.camera.world_to_screen(e.x, e.y)
        if isinstance(e, Enemy):
            add_rect(self.world_batch, sx-12, sy-18, 24, 24,
                     (210 if e.boss else 170, 40, 40))
            # 血条
            self._draw_entity_bar(sx-15, sy+10, 30, 3, e.hp / e.max_hp, (200, 40, 40))
            # 名字
            if e.boss:
                add_text(self.world_batch, e.name(), sx, sy+16, size=9, color=(255, 220, 100))
        elif isinstance(e, NPC):
            add_rect(self.world_batch, sx-11, sy-16, 22, 22, (90, 160, 230))
            add_text(self.world_batch, e.name, sx, sy+14, size=9, color=(230, 230, 230))
        elif isinstance(e, GroundItem):
            color = R.IconCache().color_of(e.icon)
            add_rect(self.world_batch, sx-5, sy-14, 10, 10, color)
        elif isinstance(e, Projectile):
            pcol = {"fireball": (255, 120, 40), "ice_spear": (120, 190, 255),
                    "arrow": (220, 190, 120), "pierce_arrow": (200, 220, 255)
                    }.get(e.kind, (230, 230, 230))
            add_circle(self.world_batch, sx, sy, 5, pcol)

    def _draw_entity_bar(self, sx, sy, w, h, pct, color):
        add_rect(self.world_batch, sx, sy, w, h, (30, 30, 30))
        add_rect(self.world_batch, sx, sy, int(w * pct), h, color)

    def _draw_player(self):
        p = self.player
        sx, sy = self.camera.world_to_screen(p.x, p.y)
        color = {"swordsman": (220, 190, 120), "knight": (150, 180, 230),
                 "mage": (200, 130, 220), "ranger": (130, 220, 150)
                 }.get(p.klass, (200, 200, 200))
        add_rect(self.world_batch, sx-9, sy-18, 18, 22, color)
        # 朝向指示
        if p.facing > 0:
            add_rect(self.world_batch, sx+9, sy-6, 5, 4, (40, 40, 40))
        else:
            add_rect(self.world_batch, sx-14, sy-6, 5, 4, (40, 40, 40))
        # 受击闪红
        if p.hit_timer > 0:
            add_rect(self.world_batch, sx-9, sy-18, 18, 22, (255, 60, 60, 160))

    def _draw_particles(self):
        for pa in self.particles.particles:
            sx, sy = self.camera.world_to_screen(pa["x"], pa["y"])
            a = int(255 * (pa["life"] / pa["max"]))
            add_circle(self.world_batch, sx, sy, pa["size"]*3, (*pa["color"], a))

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
            add_circle(self.ui_batch, self._mouse[0], self._mouse[1], 3, (250, 250, 250, 220))

    # ==================================================================
    # 输入处理
    # ==================================================================
    def on_key_press(self, symbol, modifiers):
        config.load_settings_from_json()

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

        if symbol == key._1:
            self.use_potion()
            return

        # 技能键
        skill_keys = {key.J: 0, key.K: 1, key.U: 2, key.I: 3, key.O: 4}
        if symbol in skill_keys:
            self.cast_skill_index(skill_keys[symbol])

        # 空格：翻滚/招架
        if symbol == key.SPACE:
            self._dash_or_block()

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
        self._mouse = (x, y)
        if self.mode != "playing" and self.current_menu:
            self.current_menu.motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.mode != "playing" and self.current_menu:
            self.current_menu.click(x, y)
        elif self.mode == "playing":
            self._mouse = (x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        pass
