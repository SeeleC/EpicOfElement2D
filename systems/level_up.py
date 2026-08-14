# -*- coding: utf-8 -*-
"""
升级加点系统（level_up.py）
============================
升级获得自由点数，手动或自动分配到六项属性上。
"""

ALLOC_STATS = ["hp", "mp", "atk", "defense", "crit", "crit_dmg"]
STAT_LABELS = {
    "hp": "生命", "mp": "魔法", "atk": "攻击",
    "defense": "防御", "crit": "暴击率", "crit_dmg": "暴击伤害",
}

# 各职业推荐加点
RECOMMEND = {
    "swordsman": "atk",
    "mage": "mp",
    "archer": "atk",
    "assassin": "crit",
}


class LevelUpSystem:
    def allocate(self, player, key, points=1):
        """手动分配点数到指定属性。"""
        if key not in ALLOC_STATS:
            return False
        if player.free_points < points:
            return False
        player.free_points -= points
        player.stats[key] += points
        player.refresh_stats()
        return True

    def auto_allocate(self, player):
        """按职业推荐一键加点（消耗全部自由点）。"""
        key = RECOMMEND.get(player.class_id, "atk")
        while player.free_points > 0:
            player.free_points -= 1
            player.stats[key] += 1
        player.refresh_stats()

    def recommended_stat(self, player):
        return RECOMMEND.get(player.class_id, "atk")