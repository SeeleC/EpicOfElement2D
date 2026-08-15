# -*- coding: utf-8 -*-
"""菜单界面：标题 / 职业选择 / 存档选择 / 暂停。

所有菜单都是「模式(mode)」驱动的，由 Game 状态机切换到对应界面。
"""
from . import draw_util
from .. import config
from ..registry import REGISTRY


class Button:
    def __init__(self, x, y, w, h, label, cb):
        self.x, self.y = int(x), int(y)
        self.w, self.h = w, h
        self.label = label
        self.cb = cb

    def contains(self, sx, sy):
        return (self.x <= sx <= self.x + self.w and
                self.y <= sy <= self.y + self.h)

    def draw(self, batch, hover=False):
        color = (70, 110, 160) if hover else (45, 60, 90)
        draw_util.add_rect(batch, self.x, self.y, self.w, self.h, (*color, 230))
        draw_util.add_border(batch, self.x, self.y, self.w, self.h, (0, 0, 0, 255))
        draw_util.add_text(batch, self.label,
                           self.x + self.w/2, self.y + self.h/2,
                           size=14, color=(255, 255, 255))


class Menu:
    """菜单基类：持有按钮列表与鼠标/输入处理。"""

    def __init__(self, game):
        self.game = game
        self.buttons = []
        self.hover = None

    def click(self, sx, sy):
        for b in self.buttons:
            if b.contains(sx, sy):
                b.cb()
                return

    def motion(self, sx, sy):
        for b in self.buttons:
            if b.contains(sx, sy):
                self.hover = b
                return
        self.hover = None

    def draw(self, batch):
        self.title(batch)
        for b in self.buttons:
            b.draw(batch, hover=(b is self.hover))

    def on_key(self, symbol, modifiers):
        pass

    def title(self, batch):
        pass


class TitleMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        bw, bh = 260, 46
        cx = cw/2 - bw/2
        self.buttons = [
            Button(cx, ch - 240, bw, bh, "新游戏", lambda: self.game.switch_class()),
            Button(cx, ch - 180, bw, bh, "继续游戏 (载入)", lambda: self.game.open_save_screen()),
            Button(cx, ch - 120, bw, bh, "退出", lambda: self.game.quit()),
        ]

    def title(self, batch):
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        draw_util.add_rect(batch, 0, 0, cw, ch, (18, 18, 26))
        draw_util.add_text(batch, "元素之诗：灾厄", cw/2, ch/2 + 80, size=44, color=(240, 200, 90))
        draw_util.add_text(batch, "Epic Of Elements 2D  ·  数据驱动实验", cw/2, ch/2 + 30,
                           size=16, color=(170, 170, 190))
        draw_util.add_text(batch, "by 内容数据包 驱动", cw/2, ch/2, size=13, color=(120, 120, 140))


class ClassSelectMenu(Menu):
    """新游戏 -> 选择职业。"""
    def __init__(self, game):
        super().__init__(game)
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        bw, bh = 240, 44
        cx = cw/2 - bw/2
        y = ch - 300
        self.buttons = []
        self._classes = [c for c in REGISTRY.all_of("class")]
        for i, c in enumerate(self._classes):
            self.buttons.append(Button(cx, y - i*60, bw, bh, c.get("name", c.content_id),
                                       lambda cid=c.content_id: self.game.new_game(cid)))

    def title(self, batch):
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        draw_util.add_rect(batch, 0, 0, cw, ch, (18, 18, 26))
        draw_util.add_text(batch, "选择你的职业", cw/2, ch - 60, size=28, color=(240, 200, 90))
        # 显示说明
        if self._classes:
            sel = self._classes[min(max(self.hover_idx(), 0), len(self._classes)-1)]
            desc = sel.get("desc", "无描述")
            role = sel.get("role", "")
            draw_util.add_text(batch, role, cw/2, ch - 380, size=16, color=(180, 200, 220))
            # 多行描述
            lines = self._wrap(desc, 56)
            _y = ch - 410
            for ln in lines:
                draw_util.add_text(batch, ln, cw/2, _y, size=13, color=(200, 200, 200))
                _y -= 22

    def hover_idx(self):
        if self.hover is None:
            return 0
        for i, b in enumerate(self.buttons):
            if b is self.hover:
                return i
        return 0

    def _wrap(self, s, width):
        out, cur = [], ""
        for ch in s:
            if len(cur) >= width:
                out.append(cur)
                cur = ""
            cur += ch
        if cur:
            out.append(cur)
        return out


class SaveScreen(Menu):
    """存档选择（3 个存档位）。"""
    def __init__(self, game):
        super().__init__(game)
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        bw, bh = 360, 50
        cx = cw/2 - bw/2
        self.buttons = []
        slots = game.save_manager.list_saves()
        y = ch - 150
        for i in range(1, 4):
            info = slots.get(i, {})
            exists = info.get("exists", False)
            label = info.get("name", f"空存档位 {i}")
            if exists:
                label += f"  (Lv{info.get('level')} {info.get('klass')})"
            self.buttons.append(Button(cx, y - (i-1)*64, bw, bh, label,
                                       lambda s=i: self.game.load_slot(s)))

    def title(self, batch):
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        draw_util.add_rect(batch, 0, 0, cw, ch, (18, 18, 26))
        draw_util.add_text(batch, "选择存档", cw/2, ch - 60, size=28, color=(240, 200, 90))


class PauseMenu(Menu):
    def __init__(self, game):
        super().__init__(game)
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        bw, bh = 240, 44
        cx = cw/2 - bw/2
        self.buttons = [
            Button(cx, ch/2+40, bw, bh, "继续游戏", lambda: self.game.resume()),
            Button(cx, ch/2-16, bw, bh, "保存游戏", lambda: self.game.quick_save()),
            Button(cx, ch/2-72, bw, bh, "保存并回主菜单", lambda: self.game.save_and_menu()),
        ]

    def title(self, batch):
        cw, ch = config.Graphics.WINDOW_W, config.Graphics.WINDOW_H
        draw_util.add_rect(batch, 0, 0, cw, ch, (0, 0, 0, 170))
        draw_util.add_text(batch, "暂停", cw/2, ch/2 + 120, size=30, color=(255, 255, 255))
