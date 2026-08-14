# -*- coding: utf-8 -*-
"""
战斗结算系统（combat.py）
=========================
统一负责所有伤害结算：
  - 近战判定（active_hit）与投射物判定（projectile）
  - 元素克制倍率、减伤公式、暴击判定
  - 附加状态：灼烧(burn) / 中毒(poison) / 冻结(freeze)
  - 飘字（伤害数字）、命中粒子、击杀奖励（经验/金币/掉落）
"""

import random

from config import ELEMENT_WEAKNESS


class CombatSystem:
    def __init__(self):
        self.scene = None          # 由场景绑定
        self.damage_texts = []     # 飘字列表
        self._ticks = {}           # id(target) -> {状态: 累计秒数}

    # ------------------------------------------------------------------
    def bind_scene(self, scene):
        self.scene = scene

    def _is_player(self, owner):
        return owner is not None and hasattr(owner, "class_id")

    # ------------------------------------------------------------------
    # 伤害计算
    # ------------------------------------------------------------------
    def calc_damage(self, atk, mult, defense, crit_rate, crit_dmg,
                    element, target_element):
        """返回 (伤害, 是否暴击, 元素倍率)。"""
        el_mult = 1.0
        if element and target_element:
            weak = ELEMENT_WEAKNESS.get(target_element, {})
            el_mult = weak.get(element, 1.0)
        base = atk * mult * el_mult
        dmg = max(1, int(base * (100.0 / (100.0 + defense))))   # 减伤
        crit = random.random() < crit_rate
        if crit:
            dmg = int(dmg * crit_dmg)
        return dmg, crit, el_mult

    # ------------------------------------------------------------------
    # 判定结算
    # ------------------------------------------------------------------
    def resolve_hit(self, hit):
        """结算一个近战判定（玩家/敌人的 active_hit）。"""
        if not hit or not self.scene:
            return
        if self._is_player(hit["owner"]):
            targets = self.scene.enemies
        else:
            targets = [self.scene.player] if self.scene.player else []
        for target in targets:
            if target is None or not getattr(target, "alive", True):
                continue
            if id(target) in hit["hit_set"]:
                continue
            if not hit["rect"].colliderect(target.rect):
                continue
            hit["hit_set"].add(id(target))
            self._deal(hit, target)
        hit["hit_set"].clear()   # 一帧一次，避免跨帧重复结算

    def resolve_projectile(self, proj):
        """结算投射物（命中第一个目标）。"""
        if not self.scene:
            return
        if self._is_player(proj.owner):
            targets = self.scene.enemies
            on_player = False
        else:
            targets = [self.scene.player]
            on_player = True
        for target in targets:
            if target is None or not getattr(target, "alive", True):
                continue
            if id(target) in proj.hit_set:
                continue
            if not proj.rect.colliderect(target.rect):
                continue
            proj.hit_set.add(id(target))
            hit = {
                "atk": proj.atk, "mult": proj.mult,
                "hit_count": proj.hit_count, "element": proj.element,
                "crit_rate": proj.crit_rate, "crit_dmg": proj.crit_dmg,
                "effects": proj.effects, "owner": proj.owner,
            }
            for _ in range(proj.hit_count):
                self._deal(hit, target)
            if proj.pierce <= 0:
                proj.dead = True
                break
            proj.pierce -= 1

    # ------------------------------------------------------------------
    # 实际扣血 / 奖励 / 状态
    # ------------------------------------------------------------------
    def _deal(self, hit, target):
        dmg, crit, el_mult = self.calc_damage(
            hit["atk"], hit["mult"], target.defense,
            hit["crit_rate"], hit["crit_dmg"],
            hit["element"], getattr(target, "element", None))

        target.take_damage(dmg)

        # 飘字
        color = (255, 220, 60) if crit else (255, 255, 255)
        self.spawn_text(target.rect.centerx, target.rect.top - 8,
                        dmg, color, crit=crit)

        # 命中粒子
        if self.scene and hasattr(self.scene, "particles"):
            el = hit["element"]
            self.scene.particles.hit_effect(target.rect.centerx,
                                            target.rect.centery,
                                            (255, 180, 80) if el else (255, 255, 255),
                                            is_crit=crit)
            if el:
                self.scene.particles.element_effect(target.rect.centerx,
                                                    target.rect.centery, el)

        # 附加状态
        self.apply_effects(target, hit.get("effects", {}))

        # 击杀处理
        if getattr(target, "dead", False):
            if self._is_player(hit["owner"]):
                self._on_kill_by_player(hit["owner"], target)

    def _on_kill_by_player(self, player, enemy):
        player.gain_exp(enemy.exp)
        player.gold += enemy.gold_drop
        player.kills += 1
        if self.scene and hasattr(self.scene, "on_enemy_killed"):
            self.scene.on_enemy_killed(enemy)

    # ------------------------------------------------------------------
    # 状态效果
    # ------------------------------------------------------------------
    def apply_effects(self, target, effects):
        if not effects:
            return
        if not hasattr(target, "status"):
            target.status = {}
        for name, dur in effects.items():
            if name in ("burn", "poison", "freeze"):
                target.status[name] = max(target.status.get(name, 0.0), float(dur))
        if id(target) not in self._ticks:
            self._ticks[id(target)] = {"burn": 0.0, "poison": 0.0}

    def tick_statuses(self, dt):
        """每帧调用：结算灼烧/中毒伤害，冻结时让敌人无法行动。"""
        if not self.scene:
            return
        for enemy in self.scene.enemies:
            if not getattr(enemy, "alive", True):
                continue
            status = getattr(enemy, "status", {})
            ticks = self._ticks.setdefault(id(enemy), {"burn": 0.0, "poison": 0.0})

            if status.get("freeze", 0) > 0:
                status["freeze"] -= dt
                enemy.vx = 0.0                       # 冻结：无法移动
                enemy.attack_cd = max(enemy.attack_cd, 0.3)  # 无法攻击
                if status["freeze"] <= 0:
                    status.pop("freeze", None)

            for name, per_sec in (("burn", 6), ("poison", 4)):
                if status.get(name, 0) > 0:
                    status[name] -= dt
                    ticks[name] += dt
                    if ticks[name] >= 1.0:
                        ticks[name] -= 1.0
                        dmg = int(enemy.max_hp * 0.02) if name == "poison" else 15
                        enemy.take_damage(dmg)
                        self.spawn_text(enemy.rect.centerx, enemy.rect.top - 8,
                                        dmg, (255, 140, 60) if name == "burn"
                                        else (140, 220, 80))
                    if status[name] <= 0:
                        status.pop(name, None)

    # ------------------------------------------------------------------
    # 飘字
    # ------------------------------------------------------------------
    def spawn_text(self, x, y, text, color=(255, 255, 255), crit=False):
        self.damage_texts.append({
            "x": x, "y": y, "text": str(text), "color": color,
            "life": 0.9, "crit": crit,
        })

    def update_texts(self, dt):
        keep = []
        for t in self.damage_texts:
            t["life"] -= dt
            t["y"] -= 46 * dt
            if t["life"] > 0:
                keep.append(t)
        self.damage_texts = keep