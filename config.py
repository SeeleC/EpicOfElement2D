# -*- coding: utf-8 -*-
"""
《元素之诗：灾厄》2D 版 —— 全局配置（config.py）
==================================================
本文件是项目的“总开关”：窗口参数、颜色、稀有度、职业属性、
成长曲线、伤害公式系数、默认键位与键位存档读写都集中在这里。

设计原则：
  1. 数据驱动：想改数值/颜色/键位，只改这里即可；
  2. 键位支持运行时修改，并保存到 data/saves/keybinds.json；
  3. 职业、稀有度等结构同时被 物品/技能/战斗 等模块复用。

依赖：标准库 json/os + pygame（仅用于键位常量名）。
兼容：Python 3.9。
"""

import json
import os
import sys
import glob as _glob

import pygame  # 仅用于键位常量

# ---------------------------------------------------------------------------
# 一、基础信息
# ---------------------------------------------------------------------------
GAME_TITLE = "元素之诗：灾厄（2D 复刻版）"
GAME_VERSION = "0.1.0"
AUTHOR = "个人复刻项目（原作：《元素之诗：灾厄》）"

# ---------------------------------------------------------------------------
# 二、窗口与基础节奏
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 1280          # 窗口宽（像素）
WINDOW_HEIGHT = 720          # 窗口高（像素）
FPS = 60                     # 目标帧率
FULLSCREEN = False           # 是否全屏
RESIZABLE = True             # 是否允许改变窗口大小

TILE_SIZE = 32               # 场景网格边长（像素）
GRAVITY = 2400.0             # 重力加速度（像素/秒²）
MOVE_SPEED = 340.0           # 基础水平移动速度（像素/秒）

_FONT_CACHE = {}
_FONT_SIZES = {}   # id(font) -> size（供文本引擎解析字号）

# ---------------------------------------------------------------------------
# 三、目录结构（不存在会自动创建）
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
FONT_DIR = os.path.join(ASSET_DIR, "fonts")
IMG_DIR = os.path.join(ASSET_DIR, "images")
SND_DIR = os.path.join(ASSET_DIR, "sounds")
DATA_DIR = os.path.join(BASE_DIR, "data")
SAVE_DIR = os.path.join(DATA_DIR, "saves")

for _d in (ASSET_DIR, FONT_DIR, IMG_DIR, SND_DIR, DATA_DIR, SAVE_DIR):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# 四、通用颜色
# ---------------------------------------------------------------------------
COLOR = {
    "black": (10, 10, 14),
    "white": (240, 240, 240),
    "gray": (130, 130, 140),
    "light_gray": (205, 205, 210),
    "dark": (24, 24, 30),
    "panel": (26, 26, 34),
    "panel_border": (95, 95, 115),
    "hp": (235, 65, 65),
    "hp_bg": (72, 20, 20),
    "mp": (65, 135, 255),
    "mp_bg": (20, 40, 92),
    "xp": (120, 220, 120),
    "xp_bg": (28, 58, 28),
    "gold": (255, 200, 60),
    "red": (235, 65, 65),
    "green": (115, 225, 115),
    "blue": (95, 165, 255),
    "yellow": (255, 220, 85),
    "orange": (255, 150, 60),
    "purple": (205, 125, 255),
    "cyan": (95, 225, 225),
    "transparent": (0, 0, 0, 0),
}

# ---------------------------------------------------------------------------
# 五、装备 / 物品稀有度（白→红 逐级稀有）
# ---------------------------------------------------------------------------
RARITY = {
    "common":    {"name": "普通", "color": (200, 200, 200)},
    "uncommon":  {"name": "优秀", "color": (115, 225, 115)},
    "rare":      {"name": "稀有", "color": (95, 165, 255)},
    "epic":      {"name": "史诗", "color": (205, 125, 255)},
    "legendary": {"name": "传说", "color": (255, 175, 45)},
    "mythic":    {"name": "神话", "color": (235, 65, 65)},
}
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]

# ---------------------------------------------------------------------------
# 六、元素属性（原作《元素之诗》的核心概念，用于技能/附魔/弱点）
# ---------------------------------------------------------------------------
ELEMENTS = {
    "fire":    {"name": "火", "color": (255, 120, 60),   "symbol": "炎"},
    "ice":     {"name": "冰", "color": (120, 200, 255),  "symbol": "冰"},
    "thunder": {"name": "雷", "color": (255, 230, 80),   "symbol": "雷"},
    "wind":    {"name": "风", "color": (140, 240, 160),  "symbol": "风"},
    "earth":   {"name": "地", "color": (185, 140, 90),   "symbol": "地"},
    "holy":    {"name": "圣", "color": (255, 240, 180),  "symbol": "圣"},
    "dark":    {"name": "暗", "color": (170, 120, 220),  "symbol": "暗"},
}

# 怪物 / 角色对某元素的抗性倍率（1.0=普通，>1 弱点，<1 抗性）
ELEMENT_WEAKNESS = {
    "fire":    {"ice": 1.5, "fire": 0.5},
    "ice":     {"thunder": 1.5, "ice": 0.5},
    "thunder": {"earth": 1.5, "thunder": 0.5},
    "earth":   {"wind": 1.5, "earth": 0.5},
    "wind":    {"fire": 1.5, "wind": 0.5},
    "holy":    {"dark": 1.5, "holy": 0.5},
    "dark":    {"holy": 1.5, "dark": 0.5},
}

# ---------------------------------------------------------------------------
# 七、职业定义（DNF 式 4 大职业；后续可在 data/skills.py 中补充技能细节）
# ---------------------------------------------------------------------------
CLASSES = {
    "swordsman": {
        "id": "swordsman", "name": "魔剑士",
        "desc": "近战输出型职业。以魔剑驱动元素斩击，连击爽快、爆发极高，"
                "适合喜欢贴身肉搏的冒险者。",
        "color": (214, 84, 84),
        "base": {"hp": 220, "mp": 90, "atk": 20, "defense": 14,
                 "crit": 0.06, "crit_dmg": 1.6, "move_speed": 1.0},
        "growth": {"hp": 26, "mp": 9, "atk": 3.6, "defense": 1.8,
                   "crit": 0.003, "crit_dmg": 0.01},
        "skills": ["flame_slash", "frost_cleave", "thunder_dash",
                   "whirlwind", "earth_breaker", "elemental_burst"],
        "start_items": [("iron_sword", 1), ("hp_potion", 10), ("mp_potion", 5)],
    },
    "mage": {
        "id": "mage", "name": "元素法师",
        "desc": "远程爆发型职业。掌控火/冰/雷/风四大元素，范围伤害惊人，"
                "但身板脆弱，需要走位保命。",
        "color": (95, 150, 255),
        "base": {"hp": 150, "mp": 160, "atk": 24, "defense": 8,
                 "crit": 0.05, "crit_dmg": 1.5, "move_speed": 0.9},
        "growth": {"hp": 16, "mp": 18, "atk": 4.2, "defense": 1.0,
                   "crit": 0.002, "crit_dmg": 0.008},
        "skills": ["fire_ball", "ice_spike", "chain_lightning",
                   "blizzard", "meteor", "elemental_domain"],
        "start_items": [("oak_wand", 1), ("hp_potion", 8), ("mp_potion", 10)],
    },
    "archer": {
        "id": "archer", "name": "风射手",
        "desc": "远程持续输出型职业。风之弓矢攻速快、射程远，"
                "配合冰霜/爆裂箭可风筝一切敌人。",
        "color": (120, 220, 120),
        "base": {"hp": 170, "mp": 110, "atk": 19, "defense": 10,
                 "crit": 0.10, "crit_dmg": 1.7, "move_speed": 1.1},
        "growth": {"hp": 18, "mp": 11, "atk": 3.0, "defense": 1.1,
                   "crit": 0.005, "crit_dmg": 0.012},
        "skills": ["triple_shot", "pierce_arrow", "explosive_arrow",
                   "frost_arrow", "wind_step", "arrow_rain"],
        "start_items": [("wind_bow", 1), ("hp_potion", 10), ("mp_potion", 6)],
    },
    "assassin": {
        "id": "assassin", "name": "暗影刺客",
        "desc": "敏捷爆发型职业。背刺/影袭伤害爆炸，攻速极快，"
                "利用幻影步在战场上来去如风。",
        "color": (160, 120, 220),
        "base": {"hp": 165, "mp": 120, "atk": 21, "defense": 11,
                 "crit": 0.15, "crit_dmg": 1.9, "move_speed": 1.25},
        "growth": {"hp": 19, "mp": 12, "atk": 3.4, "defense": 1.2,
                   "crit": 0.006, "crit_dmg": 0.015},
        "skills": ["shadow_strike", "rapid_stab", "dark_poison",
                   "mirage_step", "backstab", "death_dance"],
        "start_items": [("shadow_dagger", 1), ("hp_potion", 10), ("mp_potion", 5)],
    },
}

# 职业在“选择角色”界面中的展示顺序
CLASS_ORDER = ["swordsman", "mage", "archer", "assassin"]

# 角色基础属性键（供所有系统统一使用）
STAT_KEYS = ("hp", "mp", "atk", "defense", "crit", "crit_dmg", "move_speed")

# ---------------------------------------------------------------------------
# 八、等级与经验
# ---------------------------------------------------------------------------
START_LEVEL = 1
MAX_LEVEL = 60              # 参考原作 60 级封顶
EXP_BASE = 60               # 经验基数


def exp_for_level(level: int) -> int:
    """返回从 level 级升到 level+1 级所需的经验值。"""
    level = max(1, min(int(level), MAX_LEVEL))
    if level >= MAX_LEVEL:
        return 0
    raw = EXP_BASE * (level ** 1.35)
    # 向上取整到 10
    return int((raw + 5) // 10 * 10) or 10

# ---------------------------------------------------------------------------
# 九、伤害公式系数（DNF 式：攻防差 + 减伤曲线 + 暴击）
# ---------------------------------------------------------------------------
DEFENSE_DIMINISH = 200.0     # 减伤 = 防御 / (防御 + 200)
BASE_CRIT_DMG = 1.5          # 默认暴击伤害倍率
DAMAGE_VARIANCE = (0.92, 1.08)  # 伤害浮动区间
COMBO_WINDOW = 0.8           # 连击判定窗口（秒）


def calc_damage(atk: float, skill_mult: float, defense: float,
                crit_rate: float = 0.0, crit_dmg: float = BASE_CRIT_DMG,
                element_mult: float = 1.0) -> tuple:
    """计算一次攻击的最终伤害与是否暴击。

    公式：减伤 = 防御/(防御+200)；
          基础 = atk * skill_mult * element_mult * (1 - 减伤) * 浮动；
          暴击 = 基础 * crit_dmg。
    返回 (伤害, 是否暴击)。
    """
    import random
    reduction = max(0.0, min(0.95, defense / (defense + DEFENSE_DIMINISH)))
    variance = random.uniform(*DAMAGE_VARIANCE)
    base = atk * skill_mult * element_mult * (1.0 - reduction) * variance
    is_crit = random.random() < crit_rate
    dmg = base * (crit_dmg if is_crit else 1.0)
    return max(1, int(dmg)), is_crit

# 金钱单位
CURRENCY_NAME = "金币"

# ---------------------------------------------------------------------------
# 十、默认键位（DNF 风格，可运行时修改并保存）
# ---------------------------------------------------------------------------
DEFAULT_KEYBINDS = {
    # ---- 移动 ----
    "move_left":   "K_a",         # 左移
    "move_right":  "K_d",         # 右移
    "jump":        "K_w",         # 跳跃
    "crouch":      "K_s",         # 下蹲
    "dodge":       "K_SPACE",     # 闪避 / 后跳
    # ---- 战斗 ----
    "attack":      "K_j",         # 普攻
    "skill_1":     "K_u",         # 技能栏 1
    "skill_2":     "K_i",         # 技能栏 2
    "skill_3":     "K_o",         # 技能栏 3
    "skill_4":     "K_l",         # 技能栏 4
    "skill_5":     "K_SEMICOLON", # 技能栏 5
    "skill_6":     "K_QUOTE",     # 技能栏 6
    # ---- 快捷道具 ----
    "pot_1":       "K_1",         # 快捷栏 1（红药）
    "pot_2":       "K_2",         # 快捷栏 2（蓝药）
    "pot_3":       "K_3",         # 快捷栏 3
    "pot_4":       "K_4",         # 快捷栏 4
    # ---- 交互 / 界面 ----
    "interact":    "K_e",         # 对话 / 拾取 / 开箱
    "inventory":   "K_b",         # 背包
    "skill_tree":  "K_c",         # 技能树
    "quest":       "K_q",         # 任务面板
    "map":         "K_m",         # 地图
    "settings":    "K_ESCAPE",    # 暂停 / 设置（键位修改入口）
}

# 键位的人读名称（用于设置界面展示）
_KEY_NAMES = {
    "K_a": "A", "K_b": "B", "K_c": "C", "K_d": "D", "K_e": "E",
    "K_f": "F", "K_g": "G", "K_h": "H", "K_i": "I", "K_j": "J",
    "K_k": "K", "K_l": "L", "K_m": "M", "K_n": "N", "K_o": "O",
    "K_p": "P", "K_q": "Q", "K_r": "R", "K_s": "S", "K_t": "T",
    "K_u": "U", "K_v": "V", "K_w": "W", "K_x": "X", "K_y": "Y",
    "K_z": "Z",
    "K_1": "1", "K_2": "2", "K_3": "3", "K_4": "4", "K_5": "5",
    "K_6": "6", "K_7": "7", "K_8": "8", "K_9": "9", "K_0": "0",
    "K_SPACE": "空格", "K_ESCAPE": "ESC", "K_TAB": "Tab",
    "K_LSHIFT": "左Shift", "K_RSHIFT": "右Shift", "K_LCTRL": "左Ctrl",
    "K_RCTRL": "右Ctrl", "K_LALT": "左Alt", "K_RALT": "右Alt",
    "K_UP": "↑", "K_DOWN": "↓", "K_LEFT": "←", "K_RIGHT": "→",
    "K_SEMICOLON": ";", "K_QUOTE": "'", "K_COMMA": ",", "K_PERIOD": ".",
    "K_SLASH": "/", "K_BACKSLASH": "\\", "K_MINUS": "-", "K_EQUALS": "=",
    "K_LBRACKET": "[", "K_RBRACKET": "]", "K_BACKQUOTE": "`",
}


def human_key_name(keyname: str) -> str:
    """把 pygame 键位常量名转为可读名称。"""
    if keyname in _KEY_NAMES:
        return _KEY_NAMES[keyname]
    const = getattr(pygame, keyname, None)
    if const is not None:
        try:
            name = pygame.key.name(const)
            return name.upper() if name else keyname
        except Exception:
            pass
    return keyname


def key_const(keyname: str):
    """键位常量名 -> pygame 键常量（不存在返回 None）。"""
    return getattr(pygame, keyname, None)


KEYBINDS_FILE = os.path.join(SAVE_DIR, "keybinds.json")


def load_keybinds() -> dict:
    """读取保存的键位；没有或损坏时使用默认键位。"""
    binds = dict(DEFAULT_KEYBINDS)
    try:
        with open(KEYBINDS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            for action, keyname in saved.items():
                if (action in DEFAULT_KEYBINDS
                        and isinstance(keyname, str)
                        and hasattr(pygame, keyname)):
                    binds[action] = keyname
    except (OSError, ValueError):
        pass
    return binds


def save_keybinds(binds: dict) -> None:
    """把键位保存到磁盘。"""
    try:
        with open(KEYBINDS_FILE, "w", encoding="utf-8") as f:
            json.dump(binds, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        print("[config] 保存键位失败：", exc)


def action_from_key(binds: dict, key) -> str:
    """根据 pygame 按键常量反查动作名（用于键位重映射 / 操作判定）。"""
    for action, keyname in binds.items():
        if getattr(pygame, keyname, None) == key:
            return action
    return None

# ---------------------------------------------------------------------------
# 十一、字体（中文支持）
# ---------------------------------------------------------------------------


def find_cjk_font() -> str:
    """查找系统中文字体路径；找不到返回 None。"""
    candidates = [
        # Windows
        r"C:/Windows/Fonts/msyh.ttc",
        r"C:/Windows/Fonts/msyhbd.ttc",
        r"C:/Windows/Fonts/simhei.ttf",
        r"C:/Windows/Fonts/simsun.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def make_font(size, bold=False):
    key = (size, bold)
    f = _FONT_CACHE.get(key)
    if f is None:
        path = globals().get("FONT_PATH", None)
        try:
            f = pygame.font.Font(path, size) if path else pygame.font.Font(None, size)
        except Exception:
            f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _FONT_CACHE[key] = f
        _FONT_SIZES[id(f)] = size
    return f

# ============================================================
# 兼容层：保证 WINDOW / WIDTH / HEIGHT 可用（main.py、scene.py 依赖）
# 放在 config.py 最末尾，能看到前面所有已定义的变量。
# ============================================================
def _resolve_window():
    for name in ("WINDOW", "WINDOW_SIZE", "SCREEN_SIZE", "SCREEN", "RESOLUTION"):
        val = globals().get(name)
        if isinstance(val, (tuple, list)) and len(val) == 2:
            return tuple(int(v) for v in val)
    return (1280, 720)          # 都没有就用默认
WINDOW = _resolve_window()
WIDTH, HEIGHT = WINDOW

def _find_cjk_font():
    # 1) 项目自带字体优先
    for f in (_glob.glob(os.path.join("assets", "fonts", "*.ttf")) +
              _glob.glob(os.path.join("assets", "fonts", "*.ttc")) +
              _glob.glob(os.path.join("assets", "fonts", "*.otf"))):
        return f
    # 2) 系统字体
    cands = []
    if sys.platform.startswith("win"):
        cands = [r"C:\Windows\Fonts\msyh.ttc",     # 微软雅黑
                 r"C:\Windows\Fonts\msyhbd.ttc",
                 r"C:\Windows\Fonts\simhei.ttf",   # 黑体
                 r"C:\Windows\Fonts\simsun.ttc",   # 宋体
                 r"C:\Windows\Fonts\Deng.ttf"]     # 等线
    elif sys.platform == "darwin":
        cands = ["/System/Library/Fonts/PingFang.ttc",
                 "/System/Library/Fonts/Hiragino Sans GB.ttc",
                 "/System/Library/Fonts/STHeiti Light.ttc"]
    else:  # Linux
        cands = (_glob.glob("/usr/share/fonts/**/*CJK*", recursive=True) +
                 _glob.glob("/usr/share/fonts/**/*Noto*SC*", recursive=True) +
                 _glob.glob("/usr/share/fonts/**/*wqy*", recursive=True))
    for c in cands:
        if os.path.exists(c):
            return c
    return None
# 已有有效 FONT_PATH 就保留，否则自动探测
if "FONT_PATH" not in globals() or not os.path.exists(globals().get("FONT_PATH") or ""):
    FONT_PATH = _find_cjk_font()


if __name__ == "__main__":
    # 简单自检：可直接运行 python config.py
    print("GAME_TITLE :", GAME_TITLE)
    print("分辨率      :", WINDOW_WIDTH, "x", WINDOW_HEIGHT)
    print("职业        :", [c["name"] for c in CLASSES.values()])
    print("59 级升 60 级所需经验:", exp_for_level(59))
    print("键位数量    :", len(DEFAULT_KEYBINDS))
    print("CJK 字体    :", find_cjk_font())