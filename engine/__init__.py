# -*- coding: utf-8 -*-
"""EpicOfElement2D 数据驱动游戏引擎

这是一个仿照《Minecraft》数据包 / 匠心工艺(Class/7734) 精神构建的
*内容数据驱动* 2D ARPG 引擎。

核心理念:
    ---- 内容由 JSON 定义 ----
    所有可游玩内容(物品/职业/技能/怪物/配方/采集物/装备/任务/NPC/地图)
    都以 JSON 文件形式存放在 `content/` 目录。
    引擎 (engine/) 只负责通用的游戏逻辑与渲染，不硬编码任何具体内容。

    新增内容 = 添加一个 JSON 文件(或修改已有 JSON)，
    即类似 MC "数据包 / 模组" 的扩展方式，无需改动 Python 代码。
"""

from . import config
from . import registry
from . import content_loader

__all__ = ["config", "registry", "content_loader"]
