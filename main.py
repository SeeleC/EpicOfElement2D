# -*- coding: utf-8 -*-
"""《元素之诗：灾厄》2D 数据驱动实验 —— 程序入口。
启动方式：
    python main.py

引擎首先装载 content/ 下的所有 JSON「数据包」，随后进入标题菜单。
游戏世界 / 物品 / 技能 / 怪物 / 配方 全部由 JSON 驱动(类似 MC 数据包)。

自 pyglet 迁移至 arcade：窗口与事件循环改由 engine.game.GameWindow（arcade.Window 子类）
负责，main.py 只负责装载数据包并进入 arcade 主循环。
"""
import sys
import io


def _ensure_utf8():
    """在 Windows 下强制 UTF-8 输出，避免中文乱码。"""
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main():
    _ensure_utf8()
    try:
        import arcade
    except ImportError:
        print("未安装 arcade。请执行: pip install -r requirements.txt")
        return

    # 先装载内容数据包，失败则中止启动
    try:
        from engine.content_loader import ContentLoader
        from engine import config
        config.init_dirs()
        loader = ContentLoader()
        loader.load_all()
        print("[启动] 数据包装载完成:", loader.summary())
        # 文档一致性自检：若 README 的内容基线过旧会给出提醒（见 content_loader）
        loader.check_readme_sync()
    except Exception as e:
        print("[启动失败] 内容加载出错:", e)
        import traceback
        traceback.print_exc()
        return

    from engine.game import Game
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
