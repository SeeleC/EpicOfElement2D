# -*- coding: utf-8 -*-
"""
地图 / 关卡数据库（maps.py）
============================
场景类型：
  - town: 主城（安全区，无战斗）
  - dungeon: 副本（刷怪、掉落）
  - boss: 首领房（副本尾部）

字段说明：
  - size: 世界尺寸 [宽, 高]（像素）
  - platforms: 地面/平台矩形 [x, y, w, h]
  - npcs: 主城 NPC id 列表
  - portals: 传送门（副本入口/出口）
      {id, rect, to(目标地图), spawn(目标出生点)}
  - groups: 副本刷怪点 {rect, monsters:[(怪id, 数量)], respawn}
  - boss: 首领信息 {id, rect}
  - reward: 通关奖励 {gold, items:[(物品id, 数量, 概率)]}
"""


def make_portal(pid, x, y, w, h, to, spawn, name="", icon="portal"):
    return {"id": pid, "rect": [x, y, w, h], "to": to,
            "spawn": spawn, "name": name, "icon": icon}


def make_group(rect, monsters, respawn=20.0, triggered=False):
    return {"rect": rect, "monsters": monsters,
            "respawn": respawn, "triggered": triggered}


MAPS = {
    # ==================== 主城：风息镇 ====================
    "town": {
        "id": "town", "name": "风息镇（主城）", "type": "town",
        "level_req": 1, "size": [2400, 1600], "safe": True,
        "music": "town.ogg", "bg_color": (58, 78, 58),
        "spawn": [400, 1150],
        "platforms": [[0, 1200, 2400, 60]],
        "npcs": ["mayor", "blacksmith", "merchant", "alchemist",
                 "trainer", "innkeeper", "guard", "scholar"],
        "portals": [
            make_portal("p_cave", 2230, 1150, 60, 50, "dungeon_cave",
                        [200, 1000], "幽暗洞穴入口", "portal_cave"),
            make_portal("p_graveyard", 2280, 1150, 60, 50, "dungeon_graveyard",
                        [200, 1000], "亡者墓地入口", "portal_graveyard"),
            make_portal("p_ice", 2330, 1150, 60, 50, "dungeon_ice_ridge",
                        [200, 1000], "冰霜山脊入口", "portal_ice"),
            make_portal("p_fortress", 2380, 1150, 60, 50, "dungeon_fortress",
                        [200, 1000], "灾厄要塞入口", "portal_fortress"),
        ],
    },

    # ==================== 副本一：幽暗洞穴 ====================
    "dungeon_cave": {
        "id": "dungeon_cave", "name": "幽暗洞穴", "type": "dungeon",
        "level_req": 3, "size": [3200, 1800], "safe": False,
        "music": "cave.ogg", "bg_color": (40, 42, 50),
        "spawn": [200, 1400],
        "platforms": [[0, 1460, 3200, 60], [500, 1250, 260, 40],
                      [900, 1150, 220, 40], [1500, 1280, 280, 40],
                      [2100, 1150, 240, 40], [2700, 1250, 300, 40]],
        "groups": [
            make_group([300, 1000, 500, 400], [("slime", 4), ("bat", 2)]),
            make_group([1000, 1000, 500, 400], [("goblin", 3), ("rat", 2)]),
            make_group([1700, 1000, 500, 400], [("slime", 3), ("goblin", 2), ("bat", 2)]),
        ],
        "boss": {"id": "cave_troll", "rect": [2700, 1100, 400, 300]},
        "reward": {"gold": 300, "items": [("iron_ingot", 2, 1.0),
                                          ("steel_armor", 1, 0.3)]},
    },

    # ==================== 副本二：亡者墓地 ====================
    "dungeon_graveyard": {
        "id": "dungeon_graveyard", "name": "亡者墓地", "type": "dungeon",
        "level_req": 8, "size": [3400, 1900], "safe": False,
        "music": "graveyard.ogg", "bg_color": (45, 40, 48),
        "spawn": [200, 1500],
        "platforms": [[0, 1560, 3400, 60], [600, 1340, 260, 40],
                      [1200, 1240, 240, 40], [1900, 1360, 300, 40],
                      [2500, 1240, 260, 40], [3000, 1350, 300, 40]],
        "groups": [
            make_group([300, 1100, 500, 400], [("skeleton", 4), ("ghost", 2)]),
            make_group([1000, 1100, 500, 400], [("ghost", 3), ("necromancer", 1)]),
            make_group([1800, 1100, 500, 400], [("skeleton", 3), ("ghost", 2), ("necromancer", 1)]),
        ],
        "boss": {"id": "lich_king", "rect": [2850, 1100, 450, 360]},
        "reward": {"gold": 800, "items": [("soul_ash", 3, 1.0),
                                          ("luck_charm", 1, 0.3)]},
    },

    # ==================== 副本三：冰霜山脊 ====================
    "dungeon_ice_ridge": {
        "id": "dungeon_ice_ridge", "name": "冰霜山脊", "type": "dungeon",
        "level_req": 14, "size": [3600, 2000], "safe": False,
        "music": "ice.ogg", "bg_color": (45, 70, 85),
        "spawn": [200, 1600],
        "platforms": [[0, 1660, 3600, 60], [500, 1440, 280, 40],
                      [1000, 1320, 240, 40], [1600, 1460, 300, 40],
                      [2200, 1330, 260, 40], [2800, 1450, 320, 40]],
        "groups": [
            make_group([300, 1200, 500, 400], [("ice_slime", 3), ("snow_wolf", 2)]),
            make_group([1000, 1200, 500, 400], [("snow_wolf", 3), ("ice_elemental", 1)]),
            make_group([1700, 1200, 500, 400], [("ice_elemental", 2), ("snow_giant", 1)]),
        ],
        "boss": {"id": "banshee", "rect": [3000, 1200, 500, 400]},
        "reward": {"gold": 1600, "items": [("ice_crystal", 4, 1.0),
                                           ("storm_boots", 1, 0.3)]},
    },

    # ==================== 副本四：灾厄要塞 ====================
    "dungeon_fortress": {
        "id": "dungeon_fortress", "name": "灾厄要塞", "type": "dungeon",
        "level_req": 22, "size": [3800, 2100], "safe": False,
        "music": "fortress.ogg", "bg_color": (60, 40, 40),
        "spawn": [200, 1700],
        "platforms": [[0, 1760, 3800, 60], [500, 1540, 280, 40],
                      [1000, 1420, 260, 40], [1600, 1560, 320, 40],
                      [2200, 1430, 280, 40], [2900, 1550, 340, 40]],
        "groups": [
            make_group([300, 1300, 500, 400], [("flame_soldier", 3), ("shadow_assassin", 1)]),
            make_group([1000, 1300, 500, 400], [("shadow_assassin", 2), ("obsidian_golem", 1)]),
            make_group([1700, 1300, 500, 400], [("flame_soldier", 2), ("calamity_guard", 2)]),
        ],
        "boss": {"id": "calamity_lord", "rect": [3050, 1300, 600, 420],
                 "next": "dungeon_core"},
        "reward": {"gold": 3000, "items": [("flame_core", 3, 1.0),
                                           ("dark_shard", 3, 1.0)]},
    },

    # ==================== 最终战：灾厄之核 ====================
    "dungeon_core": {
        "id": "dungeon_core", "name": "灾厄之核", "type": "boss",
        "level_req": 28, "size": [2400, 1600], "safe": False,
        "music": "final.ogg", "bg_color": (50, 30, 55),
        "spawn": [200, 1200],
        "platforms": [[0, 1300, 2400, 60], [800, 1100, 300, 40],
                      [1500, 1120, 300, 40]],
        "groups": [],
        "boss": {"id": "calamity_lord", "rect": [900, 900, 800, 500],
                 "final": True},
        "reward": {"gold": 8000, "items": [("element_fragment", 5, 1.0),
                                           ("boss_trophy", 3, 1.0)]},
    },
}


def get_map(map_id):
    return MAPS.get(map_id)