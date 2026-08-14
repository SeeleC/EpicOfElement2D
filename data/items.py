# -*- coding: utf-8 -*-
"""
物品数据库（items.py）
======================
物品类型：weapon(武器) / armor(防具) / accessory(饰品)
        / consumable(消耗品) / material(材料) / quest(任务物品)

字段说明：
  - slot: 装备槽 weapon/helmet/armor/boots/necklace/ring
  - stats: 装备属性（atk攻击/defense防御/hp生命/mp魔法/crit暴击率/crit_dmg暴伤/move_speed移速）
  - use_effect: 使用效果（如 {"hp": 120}）
  - price: 商店出售价（购买价 = price * 2）
"""


def make_item(item_id, name, itype, rarity, level, desc, price,
              stack=1, slot=None, stats=None, usable=False,
              use_effect=None, subtype=None, icon=None):
    return {
        "id": item_id, "name": name, "type": itype, "rarity": rarity,
        "level": level, "desc": desc, "price": price, "stack": stack,
        "slot": slot, "stats": stats or {}, "usable": usable,
        "use_effect": use_effect, "subtype": subtype, "icon": icon or item_id,
    }


ITEMS = {
    # ===================== 武器：魔剑士 =====================
    "iron_sword": make_item("iron_sword", "铁剑", "weapon", "common", 1,
        "新手魔剑士的铁剑，平凡却可靠。", 60, slot="weapon",
        stats={"atk": 12}, subtype="sword"),
    "steel_sword": make_item("steel_sword", "精钢剑", "weapon", "uncommon", 10,
        "以精钢打造的单手剑，剑刃寒光凛冽。", 300, slot="weapon",
        stats={"atk": 30}, subtype="sword"),
    "moon_sword": make_item("moon_sword", "月华剑", "weapon", "rare", 20,
        "剑身如月光般清澈，能引动冰霜之力。", 1200, slot="weapon",
        stats={"atk": 55, "crit": 0.03}, subtype="sword"),
    "calamity_sword": make_item("calamity_sword", "灾厄大剑", "weapon", "epic", 30,
        "承载着灾厄气息的巨剑，挥动时撕裂空气。", 4800, slot="weapon",
        stats={"atk": 85, "hp": 40}, subtype="greatsword"),
    "flame_demon_blade": make_item("flame_demon_blade", "炎魔之刃", "weapon", "legendary", 40,
        "传说中封印着炎魔之力的魔剑，剑刃燃烧着永不熄灭的烈焰。", 20000, slot="weapon",
        stats={"atk": 120, "crit": 0.05, "crit_dmg": 0.1}, subtype="greatsword"),

    # ===================== 武器：元素法师 =====================
    "oak_wand": make_item("oak_wand", "橡木法杖", "weapon", "common", 1,
        "学徒法师的木质法杖，蕴藏微弱的元素之力。", 60, slot="weapon",
        stats={"atk": 12}, subtype="staff"),
    "flame_staff": make_item("flame_staff", "烈焰法杖", "weapon", "uncommon", 10,
        "杖首镶嵌火晶石，能增幅火系魔法。", 300, slot="weapon",
        stats={"atk": 32, "mp": 10}, subtype="staff"),
    "frost_staff": make_item("frost_staff", "寒霜法杖", "weapon", "rare", 20,
        "通体由冰晶凝成，触之生寒。", 1200, slot="weapon",
        stats={"atk": 58, "mp": 25}, subtype="staff"),
    "elemental_staff": make_item("elemental_staff", "元素权杖", "weapon", "epic", 30,
        "凝聚了七大元素之力的权杖，是元素使的至高信物。", 4800, slot="weapon",
        stats={"atk": 88, "mp": 40, "crit": 0.02}, subtype="staff"),
    "frost_whisper": make_item("frost_whisper", "霜语权杖", "weapon", "legendary", 40,
        "据说持有者能听到远古冰霜之龙的低语。", 20000, slot="weapon",
        stats={"atk": 122, "mp": 60, "crit_dmg": 0.12}, subtype="staff"),

    # ===================== 武器：风射手 =====================
    "wind_bow": make_item("wind_bow", "风之弓", "weapon", "common", 1,
        "以风木制成的短弓，轻盈迅捷。", 55, slot="weapon",
        stats={"atk": 11}, subtype="bow"),
    "hunter_bow": make_item("hunter_bow", "猎手长弓", "weapon", "uncommon", 10,
        "猎人们爱用的长弓，射程极远。", 280, slot="weapon",
        stats={"atk": 29, "crit": 0.02}, subtype="bow"),
    "storm_bow": make_item("storm_bow", "风暴之弓", "weapon", "rare", 20,
        "弓弦颤动时如雷霆轰鸣。", 1150, slot="weapon",
        stats={"atk": 54, "crit": 0.04}, subtype="bow"),
    "hunting_longbow": make_item("hunting_longbow", "猎风长弓", "weapon", "epic", 30,
        "为狩猎灾厄巨兽而铸的强力长弓。", 4600, slot="weapon",
        stats={"atk": 84, "crit": 0.05, "move_speed": 0.03}, subtype="bow"),
    "gods_archer_bow": make_item("gods_archer_bow", "神射手之弓", "weapon", "legendary", 40,
        "传闻为风之女神亲手所铸，箭出必中。", 20000, slot="weapon",
        stats={"atk": 118, "crit": 0.08, "crit_dmg": 0.08}, subtype="bow"),

    # ===================== 武器：暗影刺客 =====================
    "shadow_dagger": make_item("shadow_dagger", "影刃匕首", "weapon", "common", 1,
        "刺客的入门匕首，轻盈而致命。", 60, slot="weapon",
        stats={"atk": 13, "crit": 0.02}, subtype="dagger"),
    "dark_knife": make_item("dark_knife", "暗袭短刀", "weapon", "uncommon", 10,
        "涂着暗影之毒的短刀。", 300, slot="weapon",
        stats={"atk": 31, "crit": 0.03}, subtype="dagger"),
    "assassin_dagger": make_item("assassin_dagger", "刺客之刃", "weapon", "rare", 20,
        "专为暗杀而生的利刃，锋芒毕露。", 1200, slot="weapon",
        stats={"atk": 56, "crit": 0.05}, subtype="dagger"),
    "shadow_blade": make_item("shadow_blade", "暗影之刃", "weapon", "epic", 30,
        "融入暗影之力的利刃，出鞘无声。", 4800, slot="weapon",
        stats={"atk": 86, "crit": 0.06, "move_speed": 0.05}, subtype="dagger"),
    "death_kiss": make_item("death_kiss", "死亡之吻", "weapon", "legendary", 40,
        "传说中刺穿过灾厄之主的匕首，吻即死亡。", 20000, slot="weapon",
        stats={"atk": 120, "crit": 0.08, "crit_dmg": 0.1}, subtype="dagger"),

    # ===================== 防具 =====================
    "cloth_robe": make_item("cloth_robe", "布衣", "armor", "common", 1,
        "柔软的布质长袍，几乎不提供防护。", 20, slot="armor",
        stats={"defense": 2, "mp": 10}),
    "leather_armor": make_item("leather_armor", "皮甲", "armor", "common", 1,
        "轻便的皮革护甲。", 30, slot="armor", stats={"defense": 3}),
    "iron_armor": make_item("iron_armor", "铁甲", "armor", "common", 1,
        "铸铁打造的胸甲，结实耐用。", 50, slot="armor", stats={"defense": 6}),
    "steel_armor": make_item("steel_armor", "精钢战甲", "armor", "uncommon", 10,
        "精钢锻造，防御力出众。", 350, slot="armor", stats={"defense": 14}),
    "elemental_robe": make_item("elemental_robe", "元素长袍", "armor", "rare", 20,
        "织入元素丝线的法袍，魔力澎湃。", 1300, slot="armor",
        stats={"defense": 12, "mp": 40, "crit": 0.02}),
    "shadow_armor": make_item("shadow_armor", "暗影轻甲", "armor", "rare", 20,
        "轻若无物，却异常坚韧的暗影甲。", 1400, slot="armor",
        stats={"defense": 16, "crit": 0.03}),
    "calamity_armor": make_item("calamity_armor", "灾厄战甲", "armor", "epic", 30,
        "由灾厄之石淬炼而成的战甲。", 5000, slot="armor",
        stats={"defense": 24, "hp": 80}),
    "mythic_armor": make_item("mythic_armor", "神话战衣", "armor", "legendary", 40,
        "只存在于传说中的战衣，蕴含神祇之力。", 22000, slot="armor",
        stats={"defense": 32, "hp": 150, "crit": 0.02}),

    # ===================== 头盔 / 靴子 =====================
    "iron_helmet": make_item("iron_helmet", "铁盔", "armor", "common", 1,
        "普通的铁质头盔。", 30, slot="helmet", stats={"defense": 4}),
    "steel_helmet": make_item("steel_helmet", "精钢盔", "armor", "uncommon", 10,
        "防护良好的精钢头盔。", 200, slot="helmet", stats={"defense": 9}),
    "mage_crown": make_item("mage_crown", "秘法之冠", "armor", "rare", 20,
        "元素法师的象征，能安抚躁动的魔力。", 1100, slot="helmet",
        stats={"defense": 12, "hp": 30, "mp": 20}),
    "shadow_mask": make_item("shadow_mask", "暗影面罩", "armor", "rare", 20,
        "遮蔽面容的神秘面罩。", 1100, slot="helmet",
        stats={"defense": 10, "crit": 0.02}),

    "leather_boots": make_item("leather_boots", "皮靴", "armor", "common", 1,
        "轻便的皮靴。", 25, slot="boots",
        stats={"defense": 1, "move_speed": 0.02}),
    "iron_boots": make_item("iron_boots", "铁靴", "armor", "common", 1,
        "沉重的铁靴，坚固可靠。", 35, slot="boots", stats={"defense": 2}),
    "swift_boots": make_item("swift_boots", "疾风靴", "armor", "uncommon", 10,
        "以风之羽织成的靴子，身轻如燕。", 320, slot="boots",
        stats={"defense": 3, "move_speed": 0.05}),
    "storm_boots": make_item("storm_boots", "惊雷战靴", "armor", "rare", 20,
        "踏雷而行的战靴。", 1200, slot="boots",
        stats={"defense": 5, "move_speed": 0.08}),
    "shadow_steps": make_item("shadow_steps", "影步", "armor", "epic", 30,
        "融入暗影的鞋履，几乎不留痕迹。", 4600, slot="boots",
        stats={"defense": 8, "move_speed": 0.12}),

    # ===================== 饰品 =====================
    "life_necklace": make_item("life_necklace", "生命项链", "accessory", "common", 1,
        "蕴含生命气息的项链。", 120, slot="necklace", stats={"hp": 30}),
    "power_ring": make_item("power_ring", "力量戒指", "accessory", "common", 1,
        "增强力量的普通戒指。", 120, slot="ring", stats={"atk": 5}),
    "crit_ring": make_item("crit_ring", "会心戒指", "accessory", "uncommon", 10,
        "引导攻击直击要害的戒指。", 500, slot="ring", stats={"crit": 0.03}),
    "luck_charm": make_item("luck_charm", "幸运护符", "accessory", "rare", 20,
        "据说能带来好运的护符。", 1500, slot="necklace",
        stats={"crit_dmg": 0.1}),
    "battle_medal": make_item("battle_medal", "战斗勋章", "accessory", "epic", 30,
        "授予讨伐灾厄的勇士的勋章。", 5200, slot="necklace",
        stats={"atk": 12, "crit": 0.03}),
    "phoenix_necklace": make_item("phoenix_necklace", "凤凰之心", "accessory", "legendary", 40,
        "封印着不死鸟之心的项链，永不熄灭的生命之火。", 24000, slot="necklace",
        stats={"hp": 150, "mp": 80, "crit_dmg": 0.08}),

    # ===================== 消耗品 =====================
    "hp_potion": make_item("hp_potion", "生命药水", "consumable", "common", 1,
        "恢复 120 点生命。", 20, stack=99, usable=True, use_effect={"hp": 120}),
    "mp_potion": make_item("mp_potion", "魔法药水", "consumable", "common", 1,
        "恢复 80 点魔法。", 20, stack=99, usable=True, use_effect={"mp": 80}),
    "big_hp_potion": make_item("big_hp_potion", "高级生命药水", "consumable", "uncommon", 10,
        "恢复 400 点生命。", 80, stack=50, usable=True, use_effect={"hp": 400}),
    "big_mp_potion": make_item("big_mp_potion", "高级魔法药水", "consumable", "uncommon", 10,
        "恢复 250 点魔法。", 80, stack=50, usable=True, use_effect={"mp": 250}),
    "antidote": make_item("antidote", "解毒剂", "consumable", "common", 5,
        "解除中毒状态。", 30, stack=20, usable=True, use_effect={"cure": ["poison"]}),
    "scroll_return": make_item("scroll_return", "回城卷轴", "consumable", "common", 1,
        "使用后立即返回主城。", 50, stack=20, usable=True,
        use_effect={"return_town": True}),

    # ===================== 材料 =====================
    "slime_ball": make_item("slime_ball", "史莱姆凝胶", "material", "common", 1,
        "史莱姆掉落的粘稠凝胶。", 3, stack=99),
    "wolf_fang": make_item("wolf_fang", "狼牙", "material", "common", 1,
        "野狼的尖锐獠牙。", 4, stack=99),
    "goblin_ear": make_item("goblin_ear", "哥布林耳", "material", "common", 1,
        "哥布林的耳朵，猎人用来换赏金。", 5, stack=99),
    "bone_shard": make_item("bone_shard", "亡灵碎骨", "material", "uncommon", 8,
        "亡者遗骸上脱落的碎骨，萦绕着怨气。", 8, stack=99),
    "soul_ash": make_item("soul_ash", "灵魂灰烬", "material", "uncommon", 8,
        "亡灵消逝后留下的灰烬。", 10, stack=99),
    "herb": make_item("herb", "晨曦草", "material", "common", 1,
        "在晨曦下会发光的神奇药草。", 6, stack=99),
    "ice_crystal": make_item("ice_crystal", "冰晶", "material", "rare", 14,
        "冰霜山脊上凝结的纯净冰晶。", 30, stack=99),
    "flame_core": make_item("flame_core", "火焰核心", "material", "rare", 22,
        "炎魔体内燃烧的炽热核心。", 40, stack=99),
    "dark_shard": make_item("dark_shard", "暗影碎片", "material", "rare", 22,
        "灾厄气息凝结而成的暗色碎片。", 45, stack=99),
    "iron_ingot": make_item("iron_ingot", "精铁锭", "material", "uncommon", 1,
        "锻造装备的常用材料。", 25, stack=99),
    "element_fragment": make_item("element_fragment", "元素碎片", "material", "epic", 20,
        "七种元素交汇时凝结的碎片，灾厄之力的克星。", 200, stack=20),

    # ===================== 任务物品 =====================
    "mayor_letter": make_item("mayor_letter", "镇长的信", "quest", "common", 1,
        "镇长写给铁匠的推荐信，用于完成新手引导。", 0, stack=1),
    "mysterious_tome": make_item("mysterious_tome", "神秘典籍", "quest", "epic", 20,
        "记载着灾厄起源的古老典籍，字迹已模糊难辨。", 0, stack=1),
    "boss_trophy": make_item("boss_trophy", "灾厄战利品", "quest", "legendary", 1,
        "讨伐首领级魔物获得的证明。", 0, stack=10),
}


def get_item(item_id):
    """按 id 获取物品；不存在返回 None。"""
    return ITEMS.get(item_id)