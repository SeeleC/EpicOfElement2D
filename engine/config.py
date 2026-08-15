# -*- coding: utf-8 -*-
"""全局配置管理。

这里集中存放与「内容无关」的引擎参数：
窗口尺寸、分辨率、图形贴图大小、调试标志、按键绑定等。

注意：本文件保存引擎级设置；凡是「具体游戏内容」都应通过
content/*.json 定义（见 content_loader.py），不要把内容硬编码在此。
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
# 项目根目录：engine 的上两级（EpicOfElement2D/）
ROOT_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT_DIR / "content"
SAVE_DIR = ROOT_DIR / "saves"

# ---------------------------------------------------------------------------
# 图形 / 地图基础参数
# ---------------------------------------------------------------------------
# 每块地图格子的像素尺寸（饥荒式俯视角 2D，格子为正方形）。
TILE = 32

# 资源/物品图标、实体精灵都按 TILE 缩放。
ASSET_TILE = TILE

# 世界垂直方向（Y）向下为负? —— 采用传统 2D：屏幕左上角为原点，Y 向下为正。
# 世界坐标使用浮点，格子索引为 int。

# ---------------------------------------------------------------------------
# 窗口 / 渲染
# ---------------------------------------------------------------------------
class Graphics:
    WINDOW_W = 1280          # 初始窗口宽
    WINDOW_H = 720           # 初始窗口高
    FPS = 60
    VSYNC = False            # 与 asteroid.py 保持一致（非子类窗口 + 无 vsync 更稳）
    RESIZABLE = False        # 与 asteroid.py 保持一致
    TITLE = "元素之诗：灾厄 - Epic Of Elements 2D"

    # 摄像机平滑跟随系数（0~1，越大越跟手）
    CAMERA_LERP = 0.08

    # 能见到的格子数（视口近似）
    @staticmethod
    def visible_tiles():
        return (Graphics.WINDOW_W // TILE + 2, Graphics.WINDOW_H // TILE + 2)


# ---------------------------------------------------------------------------
# 颜色（RGB 元组，用于程序化绘制 / 无贴图时使用）
# ---------------------------------------------------------------------------
class Palette:
    BLACK = (0, 0, 0)
    DARK = (26, 26, 34)
    WHITE = (255, 255, 255)
    GREY = (150, 150, 150)
    RED = (200, 40, 40)
    GREEN = (60, 180, 90)
    BLUE = (70, 110, 210)
    GOLD = (220, 180, 60)
    HP = (220, 60, 60)
    MP = (70, 120, 220)
    STANCE = (230, 200, 60)

    # 六种装备品质颜色（对应 game 中的粗糙~传奇）
    QUALITY = {
        "rough":   (130, 130, 130),   # 粗糙 灰
        "common":  (200, 200, 200),   # 普通 白
        "rare":    (80, 150, 255),    # 稀有 蓝
        "superb":  (170, 90, 255),    # 极品 紫
        "epic":    (255, 170, 60),    # 史诗 橙
        "legend":  (255, 80, 80),     # 传奇 红
    }


# ---------------------------------------------------------------------------
# 默认按键绑定（可在 设置 界面或按需修改）
# ---------------------------------------------------------------------------
# 使用 pyglet.key 的符号名。
KEYS = {
    "left":    "A",
    "right":   "D",
    "up":      "W",
    "down":    "S",
    "dash":    "SPACE",      # 翻滚/闪避
    "interact": "E",          # 交互/采集/对话
    "inventory": "B",
    "char":    "C",
    "potion":  "1",
    "skill1":  "J",
    "skill2":  "K",
    "skill3":  "U",
    "skill4":  "I",
    "skill5":  "O",
    "pause":   "ESCAPE",
}


# ---------------------------------------------------------------------------
# 调试
# ---------------------------------------------------------------------------
class Debug:
    ENABLED = True      # F3 显示玩法调试
    SHOW_GRID = False   # 是否绘制网格


def init_dirs():
    """确保必要目录存在。"""
    for d in (CONTENT_DIR, SAVE_DIR):
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)


def load_settings_from_json(path=None):
    """（可选）从 settings.json 覆盖上述设置，体现数据驱动精神。"""
    import json
    path = path or (ROOT_DIR / "settings.json")
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    g = data.get("graphics")
    if g:
        for k, v in g.items():
            if hasattr(Graphics, k.upper()):
                setattr(Graphics, k.upper(), v)
