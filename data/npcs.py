# -*- coding: utf-8 -*-
"""
NPC 数据库（npcs.py）
=====================
role 角色：
  - quest: 任务发布
  - shop: 商人（出售 items 中列出的物品）
  - blacksmith: 铁匠（强化/锻造/商店）
  - trainer: 职业导师（技能学习）
  - innkeeper: 酒馆老板（情报/支线任务）
  - guard: 守卫（指引/支线任务）
  - scholar: 遗迹学者（主线剧情推进）

dialogues: {状态: 文本}，状态含 default / quest_offer / quest_progress /
           quest_done / shop 等，供对话系统读取。
"""


def make_npc(npc_id, name, role, scene, pos, dialogues, color,
             shop=None, quests=None, sprite=None, desc=""):
    return {
        "id": npc_id, "name": name, "role": role, "scene": scene,
        "pos": pos, "dialogues": dialogues, "color": color,
        "shop": shop or {}, "quests": quests or [],
        "sprite": sprite or npc_id, "desc": desc,
    }


NPCS = {
    "mayor": make_npc("mayor", "镇长·艾尔文", "quest", "town", (300, 1130),
        {
            "default": "欢迎来到风息镇，勇敢的冒险者。"
                       "近来灾厄气息在洞穴中蔓延，请务必小心。",
            "quest_offer": "年轻的冒险者，风息镇需要你的帮助。"
                           "去和铁匠、商人打个招呼，了解这座小镇吧。",
            "quest_progress": "先去完成我交代的事情吧，冒险者。",
            "quest_done": "干得漂亮！风息镇以你为荣。",
        },
        (200, 170, 130), quests=["q_01", "q_02"],
        desc="风息镇的镇长，温和而睿智的长者。"),

    "blacksmith": make_npc("blacksmith", "铁匠·铁锤", "blacksmith", "town", (560, 1120),
        {
            "default": "想要趁手的兵器？我的铁匠铺里应有尽有。",
            "quest_offer": "哦？镇长让你来找我？那把洞穴里的怪物清干净再说吧。",
            "quest_done": "这把剑送你了，用它去把怪物劈成两半！",
        },
        (170, 130, 100),
        shop={"weapons": ["iron_sword", "steel_sword", "moon_sword"],
              "armor": ["iron_armor", "steel_armor"],
              "materials": ["iron_ingot"]},
        quests=["q_03"], desc="风息镇唯一的铁匠，脾气火爆但手艺高超。"),

    "merchant": make_npc("merchant", "商人·莉莉", "shop", "town", (820, 1130),
        {
            "default": "来呀~便宜又好用的东西都在这里啦！",
            "quest_offer": "第一次来镇上的冒险者？这些东西给你打个折哦。",
        },
        (230, 180, 120),
        shop={"consumables": ["hp_potion", "mp_potion", "antidote", "scroll_return"],
              "accessories": ["life_necklace", "power_ring", "crit_ring"]},
        desc="精明能干的旅行商人，笑容背后是敏锐的算盘。"),

    "alchemist": make_npc("alchemist", "药剂师·草药", "shop", "town", (1080, 1120),
        {
            "default": "晨曦草熬成的药水，喝下去保你精神百倍。",
            "quest_offer": "想要更好的药水？那得先帮我采些晨曦草回来。",
            "quest_done": "好孩子，这瓶高级药水是你的谢礼。",
        },
        (120, 200, 130),
        shop={"consumables": ["hp_potion", "mp_potion", "big_hp_potion",
                              "big_mp_potion", "antidote"]},
        quests=["s_02"], desc="钻研草药之道的药剂师，瓶瓶罐罐堆满了小屋。"),

    "trainer": make_npc("trainer", "职业导师·修", "trainer", "town", (1340, 1125),
        {
            "default": "想变强吗？先练好基本功，再向我请教技能吧。",
        },
        (150, 150, 190),
        desc="曾游历四方的老战士，如今在此教导年轻的冒险者。"),

    "innkeeper": make_npc("innkeeper", "酒馆老板·玛丽", "innkeeper", "town", (1600, 1130),
        {
            "default": "欢迎光临‘风息酒馆’！这里有全镇最好的麦酒。",
            "quest_offer": "听说墓地那边又闹鬼了……要我讲给你听吗？",
        },
        (190, 160, 150),
        quests=["s_01"], desc="酒馆老板娘，消息灵通的万事通。"),

    "guard": make_npc("guard", "卫兵·铁卫", "guard", "town", (1860, 1120),
        {
            "default": "东边的洞穴近来有魔物出没，镇民都不敢靠近了。",
            "quest_offer": "你要是能清掉那些野狼，我就给你发赏金！",
            "quest_done": "漂亮！这是你的赏金，拿好。",
        },
        (120, 140, 160),
        quests=["s_01"], desc="镇上的卫兵，负责看守东边通往洞穴的路。"),

    "scholar": make_npc("scholar", "遗迹学者·索拉", "scholar", "town", (2100, 1125),
        {
            "default": "我在古卷中读到过……灾厄的源头深藏于要塞之下的‘灾厄之核’。",
            "quest_offer": "冒险者，想了解灾厄的真相吗？那就随我来吧。",
            "quest_progress": "收集足够的证据，我们才能揭开真相。",
            "quest_done": "不可思议……你做到了连我都做不到的事！",
        },
        (160, 140, 220),
        quests=["q_04", "q_05", "q_06", "q_07"],
        desc="研究古遗迹的学者，深知灾厄之力的秘密。"),
}


def get_npc(npc_id):
    return NPCS.get(npc_id)