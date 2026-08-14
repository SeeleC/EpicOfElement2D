# -*- coding: utf-8 -*-
"""
敌人实体（enemy.py）
====================
基于 data/monsters.py 数据生成的敌人：
  - 索敌 / 追击 / 回归 / 攻击（近战挥砍 / 远程弹道）
  - 受击闪白、死亡掉落（掉落表在数据中定义）
  - 精英与首领共用此类（boss=True 时参数更强）

行为类型 behavior:
  - chase: 近战追击
  - fly:   无视重力飞行
  - ranged: 保持距离远程攻击
"""

import random

import pygame

from config import GRAVITY
from data.monsters import get_monster
from entities.projectile import Projectile


class Enemy:
    def __init__(self, mid, pos=(0, 0)):
        d = get_monster(mid)
        if d is None:
            raise ValueError(f"未知怪物：{mid}")
        self.mid = mid
        self.name = d["name"]
        self.element = d["element"]
        self.max_hp = d["hp"]
        self.hp = self.max_hp
        self.atk = d["atk"]
        self.defense = d["defense"]
        self.exp = d["exp"]
        self.gold_min, self.gold_max = d["gold"]
        self.speed = d["speed"]
        self.color = d["color"]
        self.size = d["size"]
        self.behavior = d["behavior"]
        self.aggro = d["aggro"]
        self.drops = d["drops"]
        self.boss = d["boss"]
        self.skill = d.get("skill")
        self.desc = d.get("desc", "")

        w, h = self.size
        self.rect = pygame.Rect(int(pos[0]), int(pos[1]), w, h)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1
        self.on_ground = False
        self.spawn_pos = (int(pos[0]), int(pos[1]))
        self.return_dist = 900

        self.state = "idle"
        self.state_time = 0.0
        self.attack_cd = 0.0
        self.attack_windup = 0.0
        self._attack_fired = False
        self.hurt_timer = 0.0
        self.flash_timer = 0.0

        self.alive = True
        self.dead = False
        self.loot = []            # 死亡后 [(物品id, 数量), ...]
        self.gold_drop = 0
        self.active_hit = None    # 近战判定
        self.projectiles = []     # 远程弹道

    # ==================================================================
    def update(self, dt, player, platforms=(), world_rect=None):
        if not self.alive:
            return
        self.state_time += dt
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.attack_windup = max(0.0, self.attack_windup - dt)
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.hp <= 0:
            self.die()
            return

        dist = abs(player.rect.centerx - self.rect.centerx)
        self._do_ai(dt, player, dist)

        # 攻击前摇结束 -> 触发判定
        if self.state == "attack" and self.attack_windup <= 0 and not self._attack_fired:
            self._fire_attack(player)
            self.state = "chase"

        # 物理
        if self.behavior != "fly":
            self.vy = min(self.vy + GRAVITY * dt, 1300.0)
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)
        self._collide(platforms)
        if world_rect:
            self.rect.clamp_ip(world_rect)

        for p in self.projectiles:
            p.update(dt, platforms)
        self.projectiles = [p for p in self.projectiles if not p.dead]

    def _collide(self, platforms):
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

    # ==================================================================
    # AI
    # ==================================================================
    def _do_ai(self, dt, player, dist):
        # 过远回归
        if dist > self.return_dist:
            self._move_toward(self.spawn_pos[0], self.speed * 1.6)
            return

        if dist > self.aggro:
            self.state = "idle"
            self.vx = 0.0
            return

        attack_range = 90
        if self.behavior == "ranged":
            attack_range = 420
        if self.attack_cd <= 0 and dist <= attack_range \
                and abs(player.rect.centery - self.rect.centery) < 130:
            self.attack_cd = 1.4 if not self.boss else 1.8
            self.attack_windup = 0.4 if not self.boss else 0.6
            self._attack_fired = False
            self.state = "attack"
            return

        # 追击
        self.state = "chase"
        dx = player.rect.centerx - self.rect.centerx
        self.facing = 1 if dx > 0 else -1
        if self.behavior == "ranged":
            if dist < 200:
                self._move(-self.facing)      # 太近则拉开
            elif dist > 360:
                self._move(self.facing)       # 太远则接近
            else:
                self.vx = 0.0
        else:
            self._move(self.facing)

    def _move(self, direction):
        self.vx = direction * self.speed

    def _move_toward(self, target_x, speed):
        dx = target_x - self.rect.centerx
        if abs(dx) < 6:
            self.vx = 0.0
            return
        self.facing = 1 if dx > 0 else -1
        self.vx = self.facing * speed

    def _fire_attack(self, player):
        self._attack_fired = True
        if self.behavior == "ranged":
            proj = Projectile(
                self.rect.centerx, self.rect.centery - 20,
                self.facing * 420, 0,
                atk=self.atk, mult=1.0, element=self.element,
                owner=self, hit_count=1, crit_rate=0.0, crit_dmg=1.0,
                radius=10, color=(200, 80, 220), max_dist=600,
            )
            self.projectiles.append(proj)
        else:
            reach = 82 if not self.boss else 110
            r = self.rect
            if self.facing > 0:
                hit_rect = pygame.Rect(r.right, r.centery - 40, reach, 80)
            else:
                hit_rect = pygame.Rect(r.left - reach, r.centery - 40, reach, 80)
            self.active_hit = {
                "rect": hit_rect, "atk": self.atk, "mult": 1.0,
                "hit_count": 1, "element": self.element,
                "crit_rate": 0.0, "crit_dmg": 1.0, "effects": {},
                "owner": self, "hit_set": set(),
            }

    # ==================================================================
    def take_damage(self, damage):
        if not self.alive:
            return 0
        self.hp -= int(damage)
        self.hurt_timer = 0.18
        self.flash_timer = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.die()
        return int(damage)

    def die(self):
        if not self.alive:
            return
        self.alive = False
        self.dead = True
        self.loot = []
        for item_id, rate, lo, hi in self.drops:
            if random.random() <= rate:
                self.loot.append((item_id, random.randint(lo, hi)))
        self.gold_drop = random.randint(self.gold_min, self.gold_max)

    # ==================================================================
    def draw(self, surface, cam):
        if not self.alive:
            return
        sx, sy = cam.apply_point(self.rect.x, self.rect.y)
        color = (255, 255, 255) if self.flash_timer > 0 else self.color

        pygame.draw.ellipse(surface, (0, 0, 0, 90),
                            pygame.Rect(sx + 2, sy + self.rect.h - 4,
                                        self.rect.w - 4, 6))
        body = pygame.Rect(sx + 2, sy + 8, self.rect.w - 4, self.rect.h - 14)
        pygame.draw.rect(surface, (30, 30, 40), body)
        pygame.draw.rect(surface, color,
                         pygame.Rect(body.x + 3, body.y + 2,
                                     body.w - 6, body.h - 4))
        ex = sx + (self.rect.w - 8 if self.facing > 0 else 4)
        pygame.draw.circle(surface, (255, 40, 40), (ex, sy + 14), 4)
        pygame.draw.circle(surface, (255, 255, 255), (ex, sy + 14), 1)

        bar_w = self.rect.w + (20 if self.boss else 0)
        ratio = max(0.0, self.hp / self.max_hp)
        bx = sx - (10 if self.boss else 0)
        pygame.draw.rect(surface, (50, 20, 20), (bx, sy - 10, bar_w, 6))
        pygame.draw.rect(
            surface, (230, 60, 60) if not self.boss else (255, 200, 60),
            (bx, sy - 10, int(bar_w * ratio), 6))
        if self.boss:
            _draw_boss_name(surface, cam, self.name,
                            (sx + self.rect.w / 2, sy - 14))


def _draw_boss_name(surface, cam, name, pos):
    from config import make_font
    from utils import draw_text
    draw_text(surface, name, make_font(20, bold=True), (255, 220, 120),
              pos, anchor="midbottom", shadow=True)