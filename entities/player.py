# -*- coding: utf-8 -*-
"""
玩家实体（player.py）
====================
DNF 式横版玩家的核心控制：
  - 移动 / 跳跃 / 下蹲 / 闪避（后跳，带无敌帧）
  - 三段普攻连击（combo）
  - 6 技能快捷栏（近战判定 / 突进 / 远程弹道）
  - 属性、等级、经验、升级加点
  - 受击（无敌帧 + 击退 + 闪白）与死亡

输入：场景把“动作名集合”传进来（held=按住, pressed=本帧按下），
     与 config 的键位绑定解耦，键位重映射无需改这里。
"""

import pygame

from config import (CLASSES, START_LEVEL, MOVE_SPEED, GRAVITY,
                    COMBO_WINDOW, MAX_LEVEL, exp_for_level, ELEMENTS)
from data.skills import get_skill
from entities.projectile import Projectile

# ---- 操作参数 ----
JUMP_VELOCITY = -820.0       # 起跳速度
MAX_FALL = 1300.0            # 最大下落速度
DODGE_SPEED = 950.0          # 闪避速度
DODGE_TIME = 0.22            # 闪避持续时间
DODGE_COOLDOWN = 2.0         # 闪避冷却
DODGE_INVULN = 0.40          # 闪避无敌时间
ATTACK_REACH = 78            # 普攻攻击距离
COMBO_MULTS = (1.0, 1.25, 1.6)   # 三段连击倍率
SKILL_CAST_TIME = 0.18       # 技能前摇


class Player:
    def __init__(self, class_id="swordsman", name="冒险者", pos=(400, 1000)):
        cls = CLASSES[class_id]
        self.class_id = class_id
        self.class_name = cls["name"]
        self.name = name
        self.color = cls["color"]

        # ---- 等级 / 经验 ----
        self.level = START_LEVEL
        self.exp = 0
        self.gold = 500
        self.free_points = 0
        self.kills = 0

        # ---- 属性 ----
        self.stats = dict(cls["base"])
        self.growth = dict(cls["growth"])
        self.equip_bonus = {}          # 装备附加属性（equipment 模块填充）
        self.skills = list(cls["skills"])
        self.skill_cds = {}            # 技能冷却

        self.max_hp = int(self.stats["hp"])
        self.max_mp = int(self.stats["mp"])
        self.hp = self.max_hp
        self.mp = self.max_mp

        # ---- 几何 / 物理 ----
        self.rect = pygame.Rect(int(pos[0]), int(pos[1]), 40, 64)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1               # 1=右 -1=左
        self.on_ground = False
        self.crouching = False

        # ---- 状态 ----
        self.state = "idle"           # idle/run/jump/fall/crouch/attack/skill/dodge/hurt/dead
        self.state_time = 0.0
        self.held = set()             # 本帧按住的动作
        self.interact_requested = False
        self.return_town_requested = False

        # ---- 战斗计时 ----
        self.combo_count = 0
        self.combo_time = 0.0
        self.attack_pending = None
        self.attack_elapsed = 0.0
        self.hit_spawned = False
        self.skill_effect = None
        self.skill_hit_spawned = False
        self.skill_timer = 0.0
        self.dodge_timer = 0.0
        self.dodge_cd = 0.0
        self.hurt_timer = 0.0
        self.invuln_timer = 0.0
        self.flash_timer = 0.0

        # ---- 攻击判定（场景/战斗模块每帧读取并结算） ----
        self.active_hit = None
        self.projectiles = []
        self.quick_use = {}           # 快捷栏使用请求 pot_1..4

    # ==================================================================
    # 属性
    # ==================================================================
    def get_stat(self, key):
        return self.stats.get(key, 0.0) + self.equip_bonus.get(key, 0.0)

    def refresh_stats(self):
        self.max_hp = int(self.stats["hp"] + self.equip_bonus.get("hp", 0))
        self.max_mp = int(self.stats["mp"] + self.equip_bonus.get("mp", 0))
        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + int(amount))

    def restore_mp(self, amount):
        self.mp = min(self.max_mp, self.mp + int(amount))

    def use_item(self, item_id):
        """使用物品（药水等），返回是否成功。"""
        from data.items import get_item
        item = get_item(item_id)
        if not item or not item["usable"]:
            return False
        eff = item.get("use_effect") or {}
        if "hp" in eff:
            self.heal(eff["hp"])
        if "mp" in eff:
            self.restore_mp(eff["mp"])
        if eff.get("return_town"):
            self.return_town_requested = True
        return True

    # ==================================================================
    # 输入
    # ==================================================================
    def handle_input(self, held, pressed):
        """held: 按住动作集合；pressed: 本帧按下动作集合。"""
        self.held = set(held)
        if "interact" in pressed:
            self.interact_requested = True
        if "attack" in pressed:
            self.do_attack()
        for i in range(1, 7):
            act = f"skill_{i}"
            if act in pressed and (i - 1) < len(self.skills):
                self.cast_skill(self.skills[i - 1])
        if "dodge" in pressed:
            self._try_dodge()
        if "jump" in pressed:
            self._try_jump()
        for i in range(1, 5):
            if f"pot_{i}" in pressed:
                self.quick_use[i] = True

    # ==================================================================
    # 动作
    # ==================================================================
    def _try_jump(self):
        if self.on_ground and self.state not in ("skill", "dodge", "hurt", "dead"):
            self.vy = JUMP_VELOCITY
            self.on_ground = False
            self.state = "jump"

    def _try_dodge(self):
        if self.dodge_cd <= 0 and self.state not in ("skill", "hurt", "dead"):
            self.dodge_timer = DODGE_TIME
            self.dodge_cd = DODGE_COOLDOWN
            self.invuln_timer = max(self.invuln_timer, DODGE_INVULN)
            self.state = "dodge"

    def do_attack(self):
        if self.state in ("skill", "dodge", "hurt", "dead"):
            return
        self.combo_count = (self.combo_count + 1) % len(COMBO_MULTS)
        self.combo_time = 0.0
        self.attack_pending = {
            "mult": COMBO_MULTS[self.combo_count],
            "reach": ATTACK_REACH, "hit_count": 1, "element": None,
            "effects": {}, "windup": 0.06, "active": 0.12, "recovery": 0.14,
        }
        self.attack_elapsed = 0.0
        self.hit_spawned = False
        self.state = "attack"

    def cast_skill(self, skill_id):
        skill = get_skill(skill_id)
        if not skill:
            return
        if self.skill_cds.get(skill_id, 0) > 0:
            return
        if self.mp < skill["mp_cost"]:
            return
        if self.state in ("skill", "dodge", "hurt", "dead"):
            return
        self.mp -= skill["mp_cost"]
        self.skill_cds[skill_id] = skill["cooldown"]
        self.skill_effect = skill
        self.skill_hit_spawned = False
        self.skill_timer = SKILL_CAST_TIME
        self.state = "skill"

    # ==================================================================
    # 更新
    # ==================================================================
    def update(self, dt, platforms=(), world_rect=None):
        self.state_time += dt
        self.combo_time += dt
        self.dodge_cd = max(0.0, self.dodge_cd - dt)
        self.invuln_timer = max(0.0, self.invuln_timer - dt)
        self.flash_timer = max(0.0, self.flash_timer - dt)
        for sid in list(self.skill_cds):
            self.skill_cds[sid] = max(0.0, self.skill_cds[sid] - dt)
        if self.combo_time > COMBO_WINDOW:
            self.combo_count = 0

        if self.hp <= 0:
            self.state = "dead"
        else:
            self._update_state_machine()
            self._update_physics(dt, platforms, world_rect)
            self._update_combat(dt)

        for p in self.projectiles:
            p.update(dt, platforms)
        self.projectiles = [p for p in self.projectiles if not p.dead]

    def _update_state_machine(self):
        if self.hurt_timer > 0:
            self.state = "hurt"
        elif self.dodge_timer > 0:
            self.state = "dodge"
        elif self.state in ("attack", "skill"):
            pass
        else:
            if not self.on_ground:
                self.state = "jump" if self.vy < 0 else "fall"
            elif self.crouching:
                self.state = "crouch"
            elif abs(self.vx) > 15:
                self.state = "run"
            else:
                self.state = "idle"

    def _update_physics(self, dt, platforms, world_rect):
        locked = self.state in ("attack", "skill", "hurt", "dead")

        if not locked:
            target = 0.0
            if "move_left" in self.held:
                target -= MOVE_SPEED
            if "move_right" in self.held:
                target += MOVE_SPEED
            self.vx = target
            if target != 0:
                self.facing = 1 if target > 0 else -1
            self.crouching = "crouch" in self.held and self.on_ground
        elif "crouch" not in self.held:
            self.crouching = False

        if self.state == "dodge":
            self.vx = self.facing * DODGE_SPEED
            self.dodge_timer = max(0.0, self.dodge_timer - dt)
            self.vy = 0.0
        else:
            self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)

        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)
        self._collide_platforms(platforms)
        if world_rect:
            self.rect.clamp_ip(world_rect)

    def _collide_platforms(self, platforms):
        self.on_ground = False
        if self.vy < 0:
            return
        for plat in platforms:
            if (self.rect.bottom >= plat.top
                    and self.rect.bottom <= plat.top + max(abs(self.vy) + 8, 14)
                    and self.rect.right > plat.left
                    and self.rect.left < plat.right):
                self.rect.bottom = plat.top
                self.vy = 0.0
                self.on_ground = True

    def _update_combat(self, dt):
        # 普攻：前摇 -> 判定 -> 收招
        if self.state == "attack" and self.attack_pending:
            self.attack_elapsed += dt
            w = self.attack_pending["windup"]
            a = self.attack_pending["active"]
            if w <= self.attack_elapsed < w + a and not self.hit_spawned:
                self.hit_spawned = True
                self._spawn_melee_hit(self.attack_pending)
            if self.attack_elapsed >= w + a + self.attack_pending["recovery"]:
                self.attack_pending = None
                self.hit_spawned = False
                self.state = "idle"

        # 技能：前摇结束后生成效果
        if self.state == "skill" and self.skill_effect:
            self.skill_timer -= dt
            if self.skill_timer <= 0 and not self.skill_hit_spawned:
                self.skill_hit_spawned = True
                self._spawn_skill_effect(self.skill_effect)
            if self.skill_timer <= -0.12:
                self.skill_effect = None
                self.skill_hit_spawned = False
                self.skill_timer = 0.0
                self.state = "idle"

    # ==================================================================
    # 攻击生成
    # ==================================================================
    def _spawn_melee_hit(self, p):
        reach = p["reach"]
        r = self.rect
        if self.facing > 0:
            hit_rect = pygame.Rect(r.right, r.centery - 34, reach, 68)
        else:
            hit_rect = pygame.Rect(r.left - reach, r.centery - 34, reach, 68)
        self.active_hit = {
            "rect": hit_rect, "atk": self.get_stat("atk"),
            "mult": p["mult"], "hit_count": p.get("hit_count", 1),
            "element": p.get("element"),
            "crit_rate": self.get_stat("crit"),
            "crit_dmg": self.get_stat("crit_dmg"),
            "effects": p.get("effects", {}),
            "owner": self, "hit_set": set(),
        }

    def _spawn_skill_effect(self, skill):
        if skill["kind"] == "dash":
            # 突进类技能：触发闪避移动 + 沿途攻击
            self.dodge_timer = DODGE_TIME
            self.invuln_timer = max(self.invuln_timer, DODGE_INVULN * 0.8)
            self._spawn_melee_hit({
                "mult": skill["mult"], "reach": skill["range"],
                "hit_count": skill["hit_count"], "element": skill["element"],
                "effects": skill["effects"],
                "windup": 0.0, "active": 0.25, "recovery": 0.1,
            })
        elif skill["class"] in ("mage", "archer") and skill["range"] >= 300:
            self._spawn_projectile(skill)
        else:
            self._spawn_melee_hit({
                "mult": skill["mult"], "reach": skill["range"],
                "hit_count": skill["hit_count"], "element": skill["element"],
                "effects": skill["effects"],
                "windup": 0.0, "active": 0.22, "recovery": 0.1,
            })

    def _spawn_projectile(self, skill):
        el = ELEMENTS.get(skill["element"]) if skill["element"] else None
        color = el["color"] if el else (255, 220, 120)
        proj = Projectile(
            self.rect.centerx, self.rect.centery - 22,
            self.facing * 620, 0,
            atk=self.get_stat("atk"), mult=skill["mult"],
            element=skill["element"], owner=self,
            hit_count=skill["hit_count"],
            crit_rate=self.get_stat("crit"),
            crit_dmg=self.get_stat("crit_dmg"),
            effects=skill["effects"],
            radius=max(8, int(skill["radius"] * 0.4)),
            color=color, max_dist=skill["range"] + 120,
        )
        self.projectiles.append(proj)

    # ==================================================================
    # 受击 / 经验
    # ==================================================================
    def take_damage(self, damage, source_x=0, knockback=220):
        if self.invuln_timer > 0 or self.state == "dead":
            return False
        self.hp -= int(damage)
        self.invuln_timer = 0.5
        self.hurt_timer = 0.25
        self.flash_timer = 0.2
        if source_x:
            self.vx = knockback * (1 if self.rect.centerx < source_x else -1)
            self.vy = -180
        if self.hp <= 0:
            self.hp = 0
            self.state = "dead"
        return True

    def gain_exp(self, amount):
        self.exp += amount
        while self.level < MAX_LEVEL and self.exp >= exp_for_level(self.level):
            self.exp -= exp_for_level(self.level)
            self._level_up()

    def _level_up(self):
        self.level += 1
        self.free_points += 3
        for k in ("hp", "mp", "atk", "defense", "crit", "crit_dmg"):
            self.stats[k] += self.growth.get(k, 0.0)
        self.refresh_stats()
        self.hp = self.max_hp
        self.mp = self.max_mp

    # ==================================================================
    # 绘制
    # ==================================================================
    def draw(self, surface, cam):
        if self.state == "dead":
            return
        if self.invuln_timer > 0 and int(self.invuln_timer * 25) % 2 == 0:
            return
        sx, sy = cam.apply_point(self.rect.x, self.rect.y)
        color = (255, 255, 255) if self.flash_timer > 0 else self.color

        pygame.draw.ellipse(surface, (0, 0, 0, 90),
                            pygame.Rect(sx + 4, sy + 58, 32, 6))
        body = pygame.Rect(sx + 8, sy + 18, 24, 40)
        pygame.draw.rect(surface, (35, 35, 45), body)
        pygame.draw.rect(surface, color,
                         pygame.Rect(body.x + 3, body.y + 2,
                                     body.w - 6, body.h - 4))
        head_x = sx + 12 + (6 if self.facing > 0 else -6)
        pygame.draw.circle(surface, (240, 205, 175), (head_x + 8, sy + 10), 9)
        eye = head_x + 11 + (3 if self.facing > 0 else -1)
        pygame.draw.circle(surface, (20, 20, 30), (eye, sy + 9), 2)
        if self.state == "attack":
            wx = sx + (40 if self.facing > 0 else -12)
            pygame.draw.line(surface, (180, 180, 190), (sx + 20, sy + 30),
                             (wx, sy + 14), 4)