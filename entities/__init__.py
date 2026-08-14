# -*- coding: utf-8 -*-
"""
entities 包 —— 游戏实体
========================
玩家(player) / 敌人(enemy) / NPC(npc) / 投射物(projectile)。
实体只负责“自身状态与行为”，战斗结算、掉落拾取由后续 systems 处理。
"""

from entities.player import Player
from entities.enemy import Enemy
from entities.npc import NPC
from entities.projectile import Projectile

__all__ = ["Player", "Enemy", "NPC", "Projectile"]