# -*- coding: utf-8 -*-
"""
场景（scene.py）
================
把「地图 + 实体 + 系统 + 覆盖层 UI」串起来的运行单元。
每个场景 = 一张地图 + 一批敌人/NPC + 传送门 + 战利品拾取。

流程：
  handle_input(held, pressed)  <- 键鼠动作
  handle_event(events, pressed) <- UI / 覆盖层
  update(dt)                    <- 战斗、AI、拾取、传送
  draw(surface)                 <- 渲染
"""

import random

import pygame

from config import WINDOW
from data import get_map
from entities.enemy import Enemy
from entities.npc import NPC
from ui.character import CharacterPanel
from ui.dialogue import DialogueBox as DialogueUI
from ui.inventory import InventoryPanel
from ui.quest import QuestPanel
from ui.shop import ShopWindow as ShopUI
from ui.theme import THEME
from ui.widgets import draw_item_icon
from utils import draw_text as _draw_text
from particles import ParticleSystem

# ---------------------------------------------------------------- 舞台配置
STAGES = {
    "town": {
        "map": "town", "banner": "天空之城",
        "spawn": (400, 1000), "next": None, "portal": None,
        "npcs": ["mayor", "blacksmith", "merchant", "alchemist",
         "trainer", "innkeeper", "guard", "scholar"],
        "enemies": [], "loot": [],
    },
    "dungeon_1": {
        "map": "dungeon_1", "banner": "哥布林森林",
        "spawn": (90, 1000), "next": "dungeon_2", "portal": (2540, 950),
        "npcs": [], "loot": [{"item": "hp_potion", "pos": (700, 900), "count": 1}],
        "enemies": [
            {"mid": "slime", "pos": (900, 980), "count": 3, "gap": 70},
            {"mid": "wolf", "pos": (1500, 980), "count": 2, "gap": 90},
        ],
    },
    "dungeon_2": {
        "map": "dungeon_2", "banner": "地底洞窟",
        "spawn": (90, 1000), "next": "dungeon_3", "portal": (2540, 950),
        "npcs": [], "loot": [],
        "enemies": [
            {"mid": "bat", "pos": (700, 760), "count": 3, "gap": 80},
            {"mid": "goblin", "pos": (1500, 980), "count": 3, "gap": 80},
            {"mid": "skeleton", "pos": (2000, 980), "count": 1},
        ],
    },
    "dungeon_3": {
        "map": "dungeon_3", "banner": "遗迹回廊",
        "spawn": (90, 1000), "next": "dungeon_4", "portal": (2540, 950),
        "npcs": [], "loot": [],
        "enemies": [
            {"mid": "goblin", "pos": (800, 980), "count": 2, "gap": 90},
            {"mid": "skeleton", "pos": (1500, 980), "count": 2, "gap": 80},
            {"mid": "elf_archer", "pos": (2000, 860), "count": 1},
        ],
    },
    "dungeon_4": {
        "map": "dungeon_4", "banner": "深渊魔殿", "victory": True,
        "spawn": (90, 1000), "next": "town", "portal": None,
        "npcs": [], "loot": [{"item": "big_hp_potion", "pos": (1500, 900), "count": 2}],
        "enemies": [
            {"mid": "skeleton", "pos": (800, 980), "count": 2, "gap": 90},
            {"mid": "demon", "pos": (2200, 980), "count": 1},
        ],
    },
}

# ---------------------------------------------------------------- 相机
class Camera:
    def __init__(self, world_rect, view_w, view_h):
        self.x, self.y = 0.0, 0.0
        self.world = world_rect
        self.view_w, self.view_h = view_w, view_h
        self.shake_time = 0.0
        self.shake_power = 0.0

    def offset(self):
        return (int(self.x), int(self.y))

    def apply_point(self, wx, wy):
        return (wx - self.x, wy - self.y)

    def apply_rect(self, rect):
        return pygame.Rect(rect.x - self.x, rect.y - self.y,
                           rect.w, rect.h)

    def follow(self, target, dt):
        tx = target.rect.centerx - self.view_w / 2
        ty = target.rect.centery - self.view_h / 2
        k = min(1.0, 8.0 * dt)
        self.x += (tx - self.x) * k
        self.y += (ty - self.y) * k
        self._clamp()
        if self.shake_time > 0:
            self.shake_time -= dt
            self.x += random.uniform(-1, 1) * self.shake_power
            self.y += random.uniform(-1, 1) * self.shake_power

    def _clamp(self):
        if not self.world:
            return
        self.x = max(self.world.left,
                     min(self.x, self.world.right - self.view_w))
        self.y = max(self.world.top,
                     min(self.y, self.world.bottom - self.view_h))

    def add_shake(self, power=6, dur=0.3):
        self.shake_power = power
        self.shake_time = dur


# ---------------------------------------------------------------- 场景
class Scene:
    def __init__(self, game, stage_id, player, systems, spawn=None):
        self.game = game
        self.stage_id = stage_id
        self.stage = STAGES.get(stage_id, STAGES["town"])
        self.player = player
        self.systems = systems          # {"combat","inv","equip","level","quest"}

        self.combat = systems["combat"]
        self.combat.bind_scene(self)
        self.particles = ParticleSystem()
        self.dead = False
        self.time = 0.0

        # 地图（多入口 + 程序化兜底）
        self.map = get_map(self.stage["map"])
        if self.map is not None:
            self.platforms = list(getattr(self.map, "solid_rects", []))
            self.world_rect = getattr(self.map, "world_rect", None) \
                              or pygame.Rect(0, 0, 3200, 1200)
        else:
            print(f"[scene] 地图 {self.stage['map']} 不可用，使用程序化兜底地图")
            self.platforms = [pygame.Rect(0, 1100, 3200, 100)]
            self.world_rect = pygame.Rect(0, 0, 3200, 1200)

        # 相机
        self.cam = Camera(self.world_rect, WINDOW[0], WINDOW[1])

        # 实体
        self.enemies = []
        for entry in self.stage.get("enemies", []):
            x, y = entry["pos"]
            for i in range(entry.get("count", 1)):
                self.enemies.append(Enemy(entry["mid"],
                                          (x + i * entry.get("gap", 70), y)))
        self.npcs = [NPC(nid) for nid in self.stage.get("npcs", [])]

        # 传送门 / 战利品 / 横幅
        self.portal = self.stage.get("portal")
        self.next_stage = self.stage.get("next")
        self.loot = [{"kind": "item", "x": l["pos"][0], "y": l["pos"][1],
                      "item_id": l["item"], "count": l["count"]}
                     for l in self.stage.get("loot", [])]
        self.banner = self.stage.get("banner", "")
        self.banner_timer = 2.6
        self.active_boss = next((e for e in self.enemies if e.boss), None)

        # 覆盖层 UI
        self.overlay = None
        self.dialogue_sys = DialogueUI(game.dialogue)
        self.shop_win = ShopUI(game.shop)
        self.inv_panel = InventoryPanel(systems["inv"], systems["equip"])
        self.char_panel = CharacterPanel(systems["level"])
        self.quest_panel = QuestPanel(systems["quest"])

        # 初始位置
        if spawn is not None:
            self.player.rect.topleft = (int(spawn[0]), int(spawn[1]))

    # ==================================================================
    # 输入
    # ==================================================================
    def handle_input(self, held, pressed):
        self.player.handle_input(held, pressed)

    def handle_event(self, events, pressed_actions):
        """处理覆盖层 UI 事件。返回是否已消费（阻止暂停）。"""
        if self.overlay == "dialogue":
            for e in events:
                if self.dialogue_sys.handle_event(e):
                    return True
            return False
        if self.overlay == "shop":
            for e in events:
                if self.shop_win.handle_event(e):
                    return True
            return False
        if self.overlay == "inventory":
            for e in events:
                r = self.inv_panel.handle_event(e)
                if r == "close":
                    self.overlay = None
                    return True
                if r is not None:
                    return True
            return False
        if self.overlay == "character":
            for e in events:
                r = self.char_panel.handle_event(e)
                if r == "close":
                    self.overlay = None
                    return True
                if r is not None:
                    return True
            return False
        if self.overlay == "quest":
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.overlay = None
                    return True
            return False
        # 无覆盖层：打开面板
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_c:
                    self.overlay = "character"
                    return True
                if e.key == pygame.K_q:
                    self.overlay = "quest"
                    return True
        if "inventory" in pressed_actions:
            self.overlay = "inventory"
            return True
        return False

    # ==================================================================
    # 更新
    # ==================================================================
    def update(self, dt):
        self.time += dt
        self.particles.update(dt)
        self.game.toast.update(dt)
        if self.banner_timer > 0:
            self.banner_timer -= dt

        if self.overlay:
            return

        if self.player.state == "dead":
            self.dead = True
            return

        # 玩家
        self.player.update(dt, self.platforms, self.world_rect)
        self.systems["inv"].process_quick_use(self.player)
        self._handle_interact()

        # 敌人
        for e in self.enemies:
            e.update(dt, self.player, self.platforms, self.world_rect)

        # 近战判定结算
        for e in self.enemies:
            if e.active_hit:
                self.combat.resolve_hit(e.active_hit)
                e.active_hit = None
        if self.player.active_hit:
            self.combat.resolve_hit(self.player.active_hit)
            self.player.active_hit = None

        # 投射物
        self._resolve_projectiles()

        # 状态 / 飘字
        self.combat.tick_statuses(dt)
        self.combat.update_texts(dt)

        # 拾取 / 传送 / NPC 范围
        self._update_loot(dt)
        self._check_portal()
        for n in self.npcs:
            n.in_range_of(self.player)
            n.update(dt)

        # 清理
        self.enemies = [e for e in self.enemies if e.alive]
        self.active_boss = next((e for e in self.enemies if e.boss), None)
        self.cam.follow(self.player, dt)

    def _resolve_projectiles(self):
        projs = list(self.player.projectiles)
        for e in self.enemies:
            projs.extend(e.projectiles)
        for p in projs:
            self.combat.resolve_projectile(p)
        self.player.projectiles = [p for p in self.player.projectiles
                                   if not p.dead]
        for e in self.enemies:
            e.projectiles = [p for p in e.projectiles if not p.dead]

    # ==================================================================
    # 交互 / 传送
    # ==================================================================
    def _handle_interact(self):
        if not self.player.interact_requested:
            return
        self.player.interact_requested = False
        if self.portal and self._near_portal():
            self._activate_portal()
            return
        for npc in self.npcs:
            if npc.in_range_of(self.player):
                if npc.shop:
                    self.shop_win.sys.open(npc)
                    self.overlay = "shop"
                    self.game.sound.play("ui")
                    return
                self.game.dialogue.open(npc)
                self.overlay = "dialogue"
                self.game.sound.play("ui")
                return

    def _near_portal(self):
        if not self.portal:
            return False
        px, py = self.portal
        return (abs(self.player.rect.centerx - px) < 70
                and abs(self.player.rect.centery - py) < 80)

    def _check_portal(self):
        if self._near_portal() and self.next_stage:
            self.game.toast.show("按 E 进入下一区域")

    def _activate_portal(self):
        if self.stage.get("victory"):
            self.game.win()
            return
        self.game.change_stage(self.next_stage)

    # ==================================================================
    # 击杀 / 掉落
    # ==================================================================
    def on_enemy_killed(self, enemy):
        self.combat.spawn_text(enemy.rect.centerx, enemy.rect.top - 14,
                               f"+{enemy.exp} EXP", (120, 220, 120))
        if enemy.gold_drop > 0:
            self.loot.append({"kind": "gold", "x": enemy.rect.centerx,
                              "y": enemy.rect.centery, "value": enemy.gold_drop,
                              "count": 0})
        for item_id, count in enemy.loot:
            self.loot.append({"kind": "item", "x": enemy.rect.centerx,
                              "y": enemy.rect.centery,
                              "item_id": item_id, "count": count})
        self.particles.death_burst(enemy.rect.centerx, enemy.rect.centery,
                                   enemy.color)
        self.game.sound.play("kill")
        self.game.sound.play("coin")
        self.game.quest.on_kill(enemy.mid)
        if enemy.boss:
            self.cam.add_shake(10, 0.4)
            self.game.toast.show(f"击败首领：{enemy.name}！")
            if self.stage.get("victory"):
                self.game.quest.on_clear_dungeon(self.stage_id)
                self.game.win()

    def _update_loot(self, dt):
        keep = []
        for l in self.loot:
            l["y"] += 0.0
            dx = self.player.rect.centerx - l["x"]
            dy = self.player.rect.centery - l["y"]
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 110:                      # 磁吸
                sp = 420 * dt
                l["x"] += (dx / max(1, dist)) * sp
                l["y"] += (dy / max(1, dist)) * sp
            if dist < 34:                       # 拾取
                if l["kind"] == "gold":
                    self.player.gold += l["value"]
                    self.game.sound.play("coin")
                else:
                    got = self.systems["inv"].add(l["item_id"], l["count"])
                    if got > 0:
                        self.game.quest.on_collect(l["item_id"], got)
                        self.game.sound.play("coin")
                    else:
                        self.game.toast.show("背包已满！")
                continue
            keep.append(l)
        self.loot = keep

    # ==================================================================
    # 绘制
    # ==================================================================
    def draw(self, surface):
        self._render_map(surface)
        self._draw_loot(surface)
        self._draw_portal(surface)

        ents = self.npcs + self.enemies + [self.player]
        ents.sort(key=lambda e: e.rect.bottom)
        for e in ents:
            e.draw(surface, self.cam)

        projs = list(self.player.projectiles)
        for e in self.enemies:
            projs.extend(e.projectiles)
        for p in projs:
            p.draw(surface, self.cam)
        self.particles.draw(surface, self.cam)

        if self.banner_timer > 0:
            alpha = min(1.0, self.banner_timer)
            _draw_text(surface, self.stage["banner"],
                       self.game.font_banner, THEME["accent"],
                       (WINDOW[0] / 2, WINDOW[1] * 0.35),
                       anchor="center", shadow=True)

        # 覆盖层
        if self.overlay == "dialogue":
            self.dialogue_sys.draw(surface)
        elif self.overlay == "shop":
            self.shop_win.draw(surface)
        elif self.overlay == "inventory":
            self.inv_panel.draw(surface)
        elif self.overlay == "character":
            self.char_panel.draw(surface, self.player)
        elif self.overlay == "quest":
            self.quest_panel.draw(surface)

    def _render_map(self, surface):
        if not self.map:
            surface.fill((18, 20, 28))
            pygame.draw.rect(surface, (40, 46, 60),
                             pygame.Rect(0, 1100, 3200, 100))
            return
        ox, oy = self.cam.offset()
        layers = getattr(self.map, "layers", {}) or {}
        order = ["bg", "main", "fg"]
        for name in order:
            tiles = layers.get(name)
            if not tiles:
                continue
            tw = getattr(self.map, "tile_w", 32)
            th = getattr(self.map, "tile_h", 32)
            for (tx, ty), surf in tiles.items():
                sx = tx * tw - ox
                sy = ty * th - oy
                if -64 <= sx <= WINDOW[0] and -64 <= sy <= WINDOW[1]:
                    surface.blit(surf, (sx, sy))

    def _draw_loot(self, surface):
        for l in self.loot:
            sx, sy = self.cam.apply_point(l["x"], l["y"] + 10 * ((self.time * 3) % 1))
            if l["kind"] == "gold":
                pygame.draw.circle(surface, THEME["gold"], (int(sx), int(sy)), 6)
                pygame.draw.circle(surface, (140, 100, 30),
                                   (int(sx), int(sy)), 6, 1)
            else:
                from data.items import get_item
                item = get_item(l["item_id"])
                if item:
                    draw_item_icon(surface, item,
                                   pygame.Rect(int(sx) - 10, int(sy) - 10, 20, 20))

    def _draw_portal(self, surface):
        if not self.portal:
            return
        px, py = self.portal
        sx, sy = self.cam.apply_point(px, py)
        pul = 0.5 + 0.5 * ((self.time * 2) % 1)
        pygame.draw.circle(surface, (90, 60, 160),
                           (int(sx), int(sy)), int(34 + 8 * pul))
        pygame.draw.circle(surface, (170, 120, 255),
                           (int(sx), int(sy)), int(20 + 6 * pul))
        _draw_text(surface, "→", self.game.font_banner, (200, 160, 255),
                   (int(sx), int(sy)), anchor="center")