# -*- coding: utf-8 -*-
"""
任务 / 剧情数据库（quests.py）
=============================
objective 类型：
  - talk: 与 target NPC 对话
  - kill: 击杀 target 怪物 count 只
  - collect: 收集 target 物品 count 个
  - reach_level: 达到指定等级
  - clear_dungeon: 通关指定副本（含首领）

主线 q_01 ~ q_07 构成完整剧情链；支线 s_01 ~ s_03 为附加任务。
"""


def make_quest(qid, name, qtype, giver, level, desc, objectives,
               rewards, next_q=None, prev_q=None):
    return {
        "id": qid, "name": name, "type": qtype, "giver": giver,
        "level": level, "desc": desc, "objectives": objectives,
        "rewards": rewards, "next": next_q, "prev": prev_q,
    }


QUESTS = {
    # ==================== 主线剧情 ====================
    "q_01": make_quest("q_01", "初临风息镇", "main", "mayor", 1,
        "初到风息镇，与铁匠和商人交谈，熟悉这座小镇。",
        [
            {"type": "talk", "target": "blacksmith", "text": "与铁匠·铁锤交谈"},
            {"type": "talk", "target": "merchant", "text": "与商人·莉莉交谈"},
            {"type": "reach_level", "level": 2, "text": "达到 2 级"},
        ],
        {"exp": 120, "gold": 100, "items": [("hp_potion", 5)]},
        next_q="q_02"),

    "q_02": make_quest("q_02", "幽暗洞穴的骚动", "main", "mayor", 2,
        "洞穴中的史莱姆泛滥成灾，去清理它们并带回凝胶样本。",
        [
            {"type": "kill", "target": "slime", "count": 8, "text": "击杀史莱姆 ×8"},
            {"type": "collect", "target": "slime_ball", "count": 3, "text": "收集史莱姆凝胶 ×3"},
        ],
        {"exp": 300, "gold": 200, "items": [("mp_potion", 5)]},
        next_q="q_03"),

    "q_03": make_quest("q_03", "洞穴深处的阴影", "main", "blacksmith", 3,
        "洞穴深处的巨魔盘踞许久，铁匠委托你讨伐它。",
        [
            {"type": "clear_dungeon", "target": "dungeon_cave", "text": "通关【幽暗洞穴】并击败首领"},
        ],
        {"exp": 800, "gold": 500, "items": [("steel_sword", 1), ("iron_ingot", 3)]},
        next_q="q_04"),

    "q_04": make_quest("q_04", "亡者墓地的低语", "main", "scholar", 8,
        "学者索拉发现亡者墓地出现了异常的亡灵活动，前往调查。",
        [
            {"type": "clear_dungeon", "target": "dungeon_graveyard", "text": "通关【亡者墓地】并击败亡灵君王"},
        ],
        {"exp": 1800, "gold": 1000, "items": [("soul_ash", 5)]},
        next_q="q_05"),

    "q_05": make_quest("q_05", "冰霜山脊的寒风", "main", "scholar", 14,
        "冰霜山脊的女妖正在积蓄力量，必须在她彻底复苏前阻止她。",
        [
            {"type": "clear_dungeon", "target": "dungeon_ice_ridge", "text": "通关【冰霜山脊】并击败冰霜女妖"},
        ],
        {"exp": 3200, "gold": 2000, "items": [("ice_crystal", 5)]},
        next_q="q_06"),

    "q_06": make_quest("q_06", "灾厄将至", "main", "scholar", 22,
        "灾厄要塞中，灾厄之主即将完全苏醒。收集元素碎片，准备决战。",
        [
            {"type": "collect", "target": "element_fragment", "count": 3, "text": "收集元素碎片 ×3"},
            {"type": "clear_dungeon", "target": "dungeon_fortress", "text": "进攻【灾厄要塞】"},
        ],
        {"exp": 6000, "gold": 4000, "items": [("battle_medal", 1)]},
        next_q="q_07"),

    "q_07": make_quest("q_07", "终焉·灾厄之主", "main", "scholar", 28,
        "最后的决战。深入灾厄之核，终结灾厄之主·赫尔墨斯的统治！",
        [
            {"type": "clear_dungeon", "target": "dungeon_core", "text": "通关【灾厄之核】并击败灾厄之主"},
        ],
        {"exp": 15000, "gold": 10000,
         "items": [("element_fragment", 5), ("boss_trophy", 3), ("mythic_armor", 1)]}),

    # ==================== 支线任务 ====================
    "s_01": make_quest("s_01", "除狼务尽", "side", "guard", 2,
        "东边洞穴附近的野狼经常袭击商队，帮卫兵清剿它们。",
        [
            {"type": "kill", "target": "snow_wolf", "count": 5, "text": "击杀雪狼 ×5"},
            {"type": "kill", "target": "slime", "count": 5, "text": "击杀史莱姆 ×5"},
        ],
        {"exp": 200, "gold": 300, "items": [("power_ring", 1)]}),

    "s_02": make_quest("s_02", "药草采集", "side", "alchemist", 2,
        "药剂师需要晨曦草来炼制新药水，帮她在洞穴里采集一些。",
        [
            {"type": "collect", "target": "herb", "count": 4, "text": "采集晨曦草 ×4"},
        ],
        {"exp": 250, "gold": 200, "items": [("big_hp_potion", 2)]}),

    "s_03": make_quest("s_03", "亡者的遗物", "side", "innkeeper", 8,
        "酒馆老板想收集一些亡者遗物，用来研究镇上流传的怪谈。",
        [
            {"type": "collect", "target": "bone_shard", "count": 5, "text": "收集亡灵碎骨 ×5"},
        ],
        {"exp": 500, "gold": 400, "items": [("luck_charm", 1)]}),
}


def get_quest(qid):
    return QUESTS.get(qid)


def quest_chain():
    """返回主线任务链（按顺序）。"""
    chain = []
    qid = "q_01"
    while qid and qid in QUESTS:
        chain.append(qid)
        qid = QUESTS[qid]["next"]
    return chain