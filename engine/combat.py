# -*- coding: utf-8 -*-
"""战斗 / 技能释放系统。

依据技能数据包(skill.json)计算伤害与效果，生成投射物 / AOE / buff。
伤害公式简化自 wiki 描述：damage = 百分比*面板攻击 + 固定值。
"""
import math
import random
from .projectile import Projectile
from .vector2 import Vec2
from .registry import REGISTRY


class CombatSystem:
    def __init__(self, game):
        self.game = game

    # ------------------------------------------------------------------
    def cast_skill(self, player, skill_id, target_dx=1.0, target_dy=0.0):
        skill = REGISTRY.get("skill", skill_id)
        if skill is None:
            return
        klass = skill.get("class")
        if klass and klass != player.klass:
            return

        lv = min(player.level, 6) - 1
        cost = self._cost_at(skill, lv, player)
        if not player.spend_resource(cost):
            return

        damages = skill.get("damages") or []
        hit_flat = skill.get("hit_flat") or []
        pct = damages[lv] if lv < len(damages) else (damages[-1] if damages else 0)
        flat = hit_flat[lv] if lv < len(hit_flat) else (hit_flat[-1] if hit_flat else 0)

        base_atk = player.attack
        damage = pct / 100.0 * base_atk + flat

        # 依技能类型分发
        stype = skill.get("type")
        ox, oy = player.x, player.y

        if stype == "projectile":
            kind = self._proj_kind(skill)
            self.game.spawn_projectile(Projectile(
                kind, ox, oy, target_dx, target_dy,
                damage=damage,
                speed=skill.get("speed", 8.0),
                range=skill.get("range", 12),
                owner=player,
                pierce=skill.get("pierce", False),
                skill=skill,
            ))

        elif stype == "aoe":
            self.game.apply_aoe(ox + target_dx * 2, oy + target_dy * 2,
                                skill.get("range", 4), damage,
                                iface=player, skill=skill)

        elif stype == "melee":
            hits = []
            melee_range = skill.get("range", 4)
            for e in self.game.world.entities:
                if e is player or not getattr(e, "alive", False):
                    continue
                if isinstance(e, type(player)) and getattr(e, "klass", None):
                    continue
                if Vec2(e.x, e.y).dist(Vec2(ox, oy)) <= melee_range:
                    crit = self.roll_crit(player)
                    e.take_damage(damage * (1.5 if crit else 1.0), player)
                    e.apply_knockback(target_dx, target_dy, 2.0)
                    self.apply_skill_effects(e, skill, lv)
                    hits.append(e)
            self.trigger_melee_fx(player, skill)

        elif stype == "dash":
            player.vx = target_dx * player.speed * 2.2
            player.vy = target_dy * player.speed * 2.2
            for e in self.game.world.entities:
                if e is player or not getattr(e, "alive", False):
                    continue
                if Vec2(e.x, e.y).dist(Vec2(ox, oy)) <= skill.get("range", 4):
                    e.take_damage(damage, player)
                    e.apply_knockback(target_dx, target_dy, 3.0)

        elif stype == "heal":
            amount = damage
            player.heal(amount)
            for ally in self.game.get_allies(player):
                ally.heal(amount * 0.5)

        elif stype == "buff":
            buff = skill.get("buff", {})
            dur = buff.get("duration", 5)
            reduce = buff.get("damage_reduce", [])
            val = reduce[min(lv, len(reduce) - 1)] if reduce else 0
            player.add_status("damage_reduce", dur)

    # ------------------------------------------------------------------
    def _cost_at(self, skill, lv, player):
        costs = skill.get("costs")
        if costs:
            if isinstance(costs, list):
                lv = min(lv, len(costs) - 1)
                return costs[lv]
            return costs
        return skill.get("cost", 0)

    def _proj_kind(self, skill):
        return skill.get("projectile", "arrow")

    def roll_crit(self, attacker):
        return random.random() < attacker._crit_rate if hasattr(attacker, "_crit_rate") else random.random() < 0.05

    def apply_skill_effects(self, target, skill, lv):
        # 击飞/减速/牵制
        fl = skill.get("float")
        if fl:
            target.add_status("stun", fl)
        if skill.get("slow"):
            target.add_status("restrain", skill["slow"])
        if skill.get("debuff") == "vulnerable":
            target.add_status("vulnerable", skill.get("debuff_dur", 3))
        if skill.get("debuff") == "restrain":
            target.add_status("restrain", 2)

    def trigger_melee_fx(self, player, skill):
        player.attack_state = "attack"
        self.game.particles.spawn_slash(player.x, player.y)


class ParticlePool:
    """轻量粒子池（攻击/受击/命中特效），保持饥荒式手绘感。"""
    def __init__(self):
        self.particles = []

    def spawn_slash(self, x, y):
        for _ in range(8):
            self.particles.append({
                "x": x + random.uniform(-0.5, 0.5),
                "y": y + random.uniform(-0.5, 0.5),
                "vx": random.uniform(-3, 3), "vy": random.uniform(-3, 3),
                "life": 0.4, "max": 0.4, "color": (220, 220, 255),
                "size": random.uniform(1.0, 2.2),
            })

    def spawn_hit(self, x, y, color=(255, 120, 80)):
        for _ in range(6):
            self.particles.append({
                "x": x + random.uniform(-0.3, 0.3),
                "y": y + random.uniform(-0.3, 0.3),
                "vx": random.uniform(-2, 2), "vy": random.uniform(-2, 2),
                "life": 0.3, "max": 0.3, "color": color,
                "size": random.uniform(0.8, 1.6),
            })

    def update(self, dt):
        dead = []
        for i, p in enumerate(self.particles):
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                dead.append(i)
        for i in reversed(dead):
            self.particles.pop(i)
