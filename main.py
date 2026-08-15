# -*- coding: utf-8 -*-
"""《元素之诗：灾厄》2D 数据驱动实验 —— 程序入口。

启动方式： python main.py

引擎首先装载 content/ 下的所有 JSON「数据包」，随后进入标题菜单。
游戏世界 / 物品 / 技能 / 怪物 / 配方 全部由 JSON 驱动(类似 MC 数据包)。
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
        import pyglet
    except ImportError:
        print("未安装 pyglet。请执行: pip install -r requirements.txt")
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
    window = game.window

    # 完全仿照 pyglet_example/version4/asteroid.py 的窗口驱动方式：
    #  on_draw 用 @window.event 注册；事件处理器（键盘/鼠标）用 push_handlers 注册。
    @window.event
    def on_draw():
        window.clear()
        game.render()

    # 推入事件处理器：游戏本体负责 on_key_press / on_mouse_*；
    # （按键状态器 KeyStateHandler 已在 Game.__init__ 内注册到 self.keys）
    window.push_handlers(game)

    pyglet.app.run()


if __name__ == "__main__":
    main()
