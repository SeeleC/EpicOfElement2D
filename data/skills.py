# -*- coding: utf-8 -*-
"""
技能数据库（skills.py）
======================
每位职业 6 个主动技能，DNF 式技能栏（skill_1 ~ skill_6）。

字段说明：
  - element: fire/ice/thunder/wind/earth/holy/dark/None(无属性)
  - mult: 技能攻击倍率（乘以角色攻击力）
  - hit_count: 段数（多段攻击每次只乘 1 次减伤）
  - range: 射程/攻击距离（像素）
  - radius: 命中判定半径（像素）
  - kind: damage(伤害) / dash(位移突进)
  - effects: 附加状态，如 {"burn": 秒} / {"poison": 秒} / {"freeze": 秒}
"""


def make_skill(skill_id, name, klass, element, level, mp_cost, cooldown,
               mult, hit_count, range_px, radius, desc, kind="damage",
               effects=None, sound=None, anim=None):
    return {
        "id": skill_id, "name": name, "class": klass, "element": element,
        "level": level, "mp_cost": mp_cost, "cooldown": cooldown,
        "mult": mult, "hit_count": hit_count, "range": range_px,
        "radius": radius, "desc": desc, "kind": kind,
        "effects": effects or {}, "sound": sound or skill_id,
        "anim": anim or skill_id,
    }


SKILLS = {
    # ==================== 魔剑士 ====================
    "flame_slash": make_skill("flame_slash", "烈焰斩", "swordsman", "fire", 1,
        12, 3.0, 2.0, 1, 90, 70, "向前方斩出一道烈焰，造成火属性伤害。",
        effects={"burn": 3}, sound="slash_fire"),
    "frost_cleave": make_skill("frost_cleave", "寒冰裂斩", "swordsman", "ice", 5,
        16, 6.0, 2.6, 2, 100, 80, "连续两记附魔冰霜的斩击，有几率冻结敌人。",
        effects={"freeze": 1.5}, sound="slash_ice"),
    "thunder_dash": make_skill("thunder_dash", "雷霆突进", "swordsman", "thunder", 10,
        20, 8.0, 2.2, 3, 260, 50, "化身雷霆向前突进，沿途击退敌人。",
        kind="dash", sound="dash_thunder"),
    "whirlwind": make_skill("whirlwind", "旋风斩", "swordsman", "wind", 15,
        28, 10.0, 1.2, 5, 110, 110, "原地旋转挥剑，对周围敌人造成多段伤害。",
        sound="whirlwind"),
    "earth_breaker": make_skill("earth_breaker", "大地崩裂", "swordsman", "earth", 25,
        38, 14.0, 3.0, 1, 160, 130, "猛击地面，崩裂大地冲击前方敌人。",
        sound="earth_breaker"),
    "elemental_burst": make_skill("elemental_burst", "元素爆发", "swordsman", None, 35,
        60, 30.0, 4.5, 1, 240, 180, "引爆体内全部元素之力，造成毁灭性的一击。",
        sound="elemental_burst"),

    # ==================== 元素法师 ====================
    "fire_ball": make_skill("fire_ball", "火球术", "mage", "fire", 1,
        14, 2.5, 2.4, 1, 320, 40, "发射一枚炽热火球，命中后灼烧敌人。",
        effects={"burn": 3}, sound="fire_ball"),
    "ice_spike": make_skill("ice_spike", "冰锥术", "mage", "ice", 5,
        18, 5.0, 2.0, 2, 300, 50, "召唤两排冰锥贯穿敌人，有几率冻结。",
        effects={"freeze": 1.2}, sound="ice_spike"),
    "chain_lightning": make_skill("chain_lightning", "连锁闪电", "mage", "thunder", 10,
        24, 8.0, 1.8, 3, 340, 60, "释放闪电在敌人之间弹跳，最多命中3个目标。",
        sound="chain_lightning"),
    "blizzard": make_skill("blizzard", "暴风雪", "mage", "ice", 20,
        45, 16.0, 1.1, 8, 360, 140, "召唤暴风雪覆盖大范围区域，持续多段伤害。",
        effects={"freeze": 0.8}, sound="blizzard"),
    "meteor": make_skill("meteor", "陨石术", "mage", "earth", 30,
        55, 20.0, 3.5, 1, 400, 120, "召唤天外陨石轰击目标区域。",
        sound="meteor"),
    "elemental_domain": make_skill("elemental_domain", "元素领域", "mage", None, 38,
        70, 35.0, 0.8, 12, 260, 200, "张开元素领域，领域内敌人受到持续元素伤害。",
        sound="elemental_domain"),

    # ==================== 风射手 ====================
    "triple_shot": make_skill("triple_shot", "三连射", "archer", None, 1,
        10, 2.0, 0.8, 3, 360, 30, "快速射出三支箭矢。",
        sound="triple_shot"),
    "pierce_arrow": make_skill("pierce_arrow", "贯穿箭", "archer", None, 5,
        14, 4.0, 2.2, 1, 460, 40, "射出强力箭矢，贯穿直线上的所有敌人。",
        sound="pierce_arrow"),
    "explosive_arrow": make_skill("explosive_arrow", "爆裂箭", "archer", "fire", 12,
        22, 7.0, 2.6, 1, 380, 90, "射出会爆炸的箭矢，造成范围火属性伤害。",
        effects={"burn": 2}, sound="explosive_arrow"),
    "frost_arrow": make_skill("frost_arrow", "冰霜箭", "archer", "ice", 18,
        26, 8.0, 2.4, 1, 400, 60, "射出冰霜之箭，命中后减速并冻结敌人。",
        effects={"freeze": 1.0}, sound="frost_arrow"),
    "wind_step": make_skill("wind_step", "疾风步", "archer", "wind", 24,
        30, 12.0, 1.5, 2, 300, 70, "踏风后撤并射出两箭，拉开距离。",
        kind="dash", sound="wind_step"),
    "arrow_rain": make_skill("arrow_rain", "箭雨", "archer", "wind", 32,
        48, 18.0, 1.0, 10, 420, 150, "向天空射出无数箭矢，如雨般覆盖大范围。",
        sound="arrow_rain"),

    # ==================== 暗影刺客 ====================
    "shadow_strike": make_skill("shadow_strike", "影袭", "assassin", "dark", 1,
        12, 3.0, 2.1, 1, 80, 60, "化作暗影突袭敌人，附加暗属性伤害。",
        sound="shadow_strike"),
    "rapid_stab": make_skill("rapid_stab", "疾影连刺", "assassin", None, 5,
        16, 5.0, 0.7, 5, 70, 50, "以极速连刺敌人五下，触发多次暴击判定。",
        sound="rapid_stab"),
    "dark_poison": make_skill("dark_poison", "淬毒", "assassin", "dark", 10,
        20, 8.0, 1.6, 3, 80, 60, "匕首淬毒挥砍，使敌人持续中毒。",
        effects={"poison": 5}, sound="dark_poison"),
    "mirage_step": make_skill("mirage_step", "幻影步", "assassin", None, 15,
        24, 9.0, 1.8, 2, 240, 60, "留下幻影突进，本体闪现攻击。",
        kind="dash", sound="mirage_step"),
    "backstab": make_skill("backstab", "背刺", "assassin", None, 22,
        28, 10.0, 3.4, 1, 90, 70, "绕至敌人背后发动致命一击，暴击率大幅提升。",
        effects={"backstab": True}, sound="backstab"),
    "death_dance": make_skill("death_dance", "死亡圆舞曲", "assassin", "dark", 34,
        52, 20.0, 1.2, 8, 120, 100, "化身死亡之舞，对周围敌人疯狂切割。",
        sound="death_dance"),
}


def get_skill(skill_id):
    return SKILLS.get(skill_id)


def skills_of_class(class_id):
    """返回某职业的全部技能（按学习等级排序）。"""
    return sorted(
        [s for s in SKILLS.values() if s["class"] == class_id],
        key=lambda s: s["level"],
    )