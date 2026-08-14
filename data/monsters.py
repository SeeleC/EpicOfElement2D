# -*- coding: utf-8 -*-
"""
怪物数据库（monsters.py）
=========================
包含普通怪物、精英怪与首领（boss）。
掉落格式：[(物品id, 掉落率0~1, 最少数量, 最多数量), ...]
"""


def make_monster(mid, name, element, hp, atk, defense, exp, gold, speed,
                 color, size=(40, 40), behavior="chase", aggro=180,
                 drops=None, boss=False, skill=None, desc=""):
    return {
        "id": mid, "name": name, "element": element,
        "hp": hp, "atk": atk, "defense": defense,
        "exp": exp, "gold": gold, "speed": speed,
        "color": color, "size": size, "behavior": behavior,
        "aggro": aggro, "drops": drops or [], "boss": boss,
        "skill": skill, "desc": desc,
    }


MONSTERS = {
    # ==================== 幽暗洞穴 ====================
    "slime": make_monster("slime", "史莱姆", "earth", 60, 8, 3, 12, (3, 8), 60,
        (90, 220, 120), size=(36, 30), aggro=120,
        drops=[("slime_ball", 0.6, 1, 2), ("hp_potion", 0.1, 1, 1)],
        desc="洞穴中最常见的魔物，行动迟缓但数量众多。"),
    "bat": make_monster("bat", "洞穴蝙蝠", "wind", 45, 10, 2, 10, (2, 6), 120,
        (120, 100, 160), size=(30, 26), behavior="fly", aggro=160,
        drops=[("herb", 0.3, 1, 1)], desc="受惊后成群扑来的吸血蝙蝠。"),
    "goblin": make_monster("goblin", "哥布林", "dark", 90, 13, 5, 20, (6, 12), 90,
        (90, 160, 90), size=(34, 34), aggro=200,
        drops=[("goblin_ear", 0.5, 1, 1), ("hp_potion", 0.15, 1, 1)],
        desc="贪婪狡诈的小型魔物，会捡拾地上的一切。"),
    "rat": make_monster("rat", "洞窟巨鼠", "earth", 70, 11, 4, 15, (4, 9), 110,
        (140, 120, 110), size=(32, 28), aggro=170,
        drops=[("herb", 0.2, 1, 1)], desc="被灾厄气息污染的巨大老鼠。"),
    "cave_troll": make_monster("cave_troll", "洞穴巨魔·石皮", "earth", 1200, 32, 18, 300,
        (80, 120), 70, (120, 140, 120), size=(90, 100), behavior="chase",
        aggro=300, boss=True, skill="slam",
        drops=[("iron_ingot", 1.0, 2, 4), ("steel_armor", 0.3, 1, 1),
               ("steel_sword", 0.25, 1, 1), ("boss_trophy", 1.0, 1, 1)],
        desc="幽暗洞穴深处的守卫巨魔，皮糙肉厚。"),

    # ==================== 亡者墓地 ====================
    "skeleton": make_monster("skeleton", "骷髅兵", "dark", 160, 20, 10, 30, (10, 18), 80,
        (210, 210, 215), size=(34, 40), aggro=200,
        drops=[("bone_shard", 0.5, 1, 2), ("mp_potion", 0.12, 1, 1)],
        desc="从墓地爬出的亡灵士兵，手持锈剑。"),
    "ghost": make_monster("ghost", "游魂", "holy", 120, 18, 6, 28, (8, 14), 100,
        (200, 220, 255), size=(32, 40), behavior="fly", aggro=180,
        drops=[("soul_ash", 0.4, 1, 2)], desc="哀嚎的亡者之魂，穿墙而过。"),
    "necromancer": make_monster("necromancer", "亡灵法师", "dark", 220, 26, 12, 50,
        (18, 28), 70, (150, 80, 200), size=(36, 46), behavior="ranged",
        aggro=260, skill="dark_bolt",
        drops=[("soul_ash", 0.6, 1, 2), ("dark_knife", 0.1, 1, 1)],
        desc="操纵亡灵的死灵法师。"),
    "lich_king": make_monster("lich_king", "亡灵君王·阿克图斯", "dark", 3500, 48, 28,
        900, (200, 300), 60, (170, 90, 220), size=(100, 120), behavior="ranged",
        aggro=320, boss=True, skill="dark_bolt",
        drops=[("soul_ash", 1.0, 3, 5), ("frost_staff", 0.25, 1, 1),
               ("luck_charm", 0.2, 1, 1), ("boss_trophy", 1.0, 1, 1)],
        desc="亡者墓地的统治者，妄图让整个大陆陷入死寂。"),

    # ==================== 冰霜山脊 ====================
    "ice_slime": make_monster("ice_slime", "冰晶史莱姆", "ice", 260, 32, 16, 55,
        (20, 32), 55, (140, 220, 255), size=(38, 32), aggro=160,
        drops=[("ice_crystal", 0.4, 1, 2), ("big_hp_potion", 0.1, 1, 1)],
        desc="浑身结满冰晶的史莱姆，触碰生寒。"),
    "snow_wolf": make_monster("snow_wolf", "雪狼", "wind", 300, 36, 15, 60, (22, 34),
        120, (220, 220, 230), size=(46, 34), aggro=240,
        drops=[("wolf_fang", 0.6, 1, 2), ("swift_boots", 0.08, 1, 1)],
        desc="冰原上成群结队的凶猛雪狼。"),
    "ice_elemental": make_monster("ice_elemental", "冰霜元素", "ice", 280, 34, 18, 58,
        (20, 30), 70, (180, 230, 255), size=(40, 48), behavior="ranged",
        aggro=220, skill="ice_bolt",
        drops=[("ice_crystal", 0.5, 1, 2)], desc="由纯粹寒气凝聚成的元素生物。"),
    "snow_giant": make_monster("snow_giant", "雪原巨人", "earth", 650, 52, 30, 120,
        (40, 60), 55, (200, 210, 220), size=(80, 100), behavior="chase",
        aggro=260, skill="slam",
        drops=[("ice_crystal", 0.5, 1, 3), ("storm_boots", 0.08, 1, 1)],
        desc="盘踞在冰霜山脊的远古巨人。"),
    "banshee": make_monster("banshee", "冰霜女妖·赛琳", "ice", 8000, 62, 40, 2000,
        (300, 450), 85, (170, 220, 255), size=(90, 110), behavior="ranged",
        aggro=340, boss=True, skill="ice_bolt",
        drops=[("ice_crystal", 1.0, 4, 6), ("frost_whisper", 0.15, 1, 1),
               ("phoenix_necklace", 0.12, 1, 1), ("boss_trophy", 1.0, 1, 1)],
        desc="以哀嚎冻结一切的女妖，寒冰山脊的主宰。"),

    # ==================== 灾厄要塞 ====================
    "flame_soldier": make_monster("flame_soldier", "炎魔兵卒", "fire", 520, 48, 26, 110,
        (35, 50), 85, (255, 120, 60), size=(40, 46), behavior="chase",
        aggro=240,
        drops=[("flame_core", 0.35, 1, 1), ("big_hp_potion", 0.15, 1, 1)],
        desc="灾厄军团中的火焰步兵。"),
    "shadow_assassin": make_monster("shadow_assassin", "暗影刺客", "dark", 480, 55, 22,
        120, (38, 55), 150, (170, 120, 220), size=(36, 42), behavior="chase",
        aggro=280,
        drops=[("dark_shard", 0.4, 1, 1), ("big_mp_potion", 0.15, 1, 1)],
        desc="来无影去无踪的灾厄刺客。"),
    "obsidian_golem": make_monster("obsidian_golem", "黑曜石魔像", "earth", 1200, 60, 45,
        180, (60, 80), 45, (60, 60, 70), size=(90, 110), behavior="chase",
        aggro=220, skill="slam",
        drops=[("dark_shard", 0.5, 1, 2), ("calamity_armor", 0.1, 1, 1)],
        desc="由黑曜石与灾厄之力铸成的战争魔像。"),
    "calamity_guard": make_monster("calamity_guard", "灾厄护卫", "fire", 900, 58, 38,
        160, (55, 75), 90, (220, 80, 80), size=(56, 64), behavior="chase",
        aggro=260,
        drops=[("flame_core", 0.5, 1, 2), ("dark_shard", 0.4, 1, 2)],
        desc="守护灾厄之主的精英护卫。"),

    # ==================== 灾厄之核（最终BOSS） ====================
    "calamity_lord": make_monster("calamity_lord", "灾厄之主·赫尔墨斯", "dark", 20000, 85, 60,
        5000, (800, 1200), 90, (255, 70, 70), size=(120, 150), behavior="ranged",
        aggro=400, boss=True, skill="calamity_blast",
        drops=[("dark_shard", 1.0, 5, 8), ("element_fragment", 1.0, 1, 3),
               ("death_kiss", 0.2, 1, 1), ("gods_archer_bow", 0.2, 1, 1),
               ("mythic_armor", 0.2, 1, 1), ("boss_trophy", 1.0, 3, 5)],
        desc="灾厄的源头，将整个大陆拖入黑暗的最终主宰。"),
}


def get_monster(mid):
    return MONSTERS.get(mid)