# -*- coding: utf-8 -*-
"""
对话系统（dialogue.py）
=======================
NPC 交互流程：
  - 打开对话 -> 显示文本页 -> 可接任务 / 可交付任务
  - advance() 翻页，choose() 处理接受/拒绝/交付
UI 表现层由 ui/ 模块负责，本系统只管状态与文案。
"""


class DialogueSystem:
    def __init__(self, game=None):
        self.game = game
        self.npc = None
        self.lines = []
        self.page = 0
        self.prompt = None       # 交互选项 {"type":..., "qid":...}

    # ------------------------------------------------------------------
    @property
    def is_open(self):
        return self.npc is not None

    def open(self, npc):
        self.npc = npc
        self._build()

    def close(self):
        self.npc = None
        self.lines = []
        self.prompt = None
        self.page = 0

    # ------------------------------------------------------------------
    def _build(self):
        self.page = 0
        self.prompt = None
        default = self.npc.dialogues.get("default", "……")
        quest = self.game.quest if self.game else None

        if quest and self.npc.quests:
            # 1) 优先：可交付任务
            for qid in self.npc.quests:
                if quest.is_active(qid) and quest.is_completable(qid):
                    text = self.npc.dialogues.get("quest_done", default)
                    self.lines = [text, f"『{quest_name(qid)}』已达成，是否交付？"]
                    self.prompt = {"type": "quest_done", "qid": qid}
                    return
            # 2) 其次：可接任务
            avail = quest.available(self.npc.id)
            if avail:
                q = avail[0]
                text = self.npc.dialogues.get("quest_offer", default)
                self.lines = [text, f"『{q['name']}』\n{q['desc']}"]
                self.prompt = {"type": "quest_offer", "qid": q["id"]}
                return
        # 3) 默认对话
        self.lines = [default]

    def current_line(self):
        if 0 <= self.page < len(self.lines):
            return self.lines[self.page]
        return ""

    def advance(self):
        """翻页/关闭。返回是否还有下一页。"""
        if self.page < len(self.lines) - 1:
            self.page += 1
            return True
        self.close()
        return False

    # ------------------------------------------------------------------
    def choose(self, choice):
        """choice: 'accept' / 'decline' / 'done' / 'close'"""
        if self.prompt is None:
            self.close()
            return
        pt, qid = self.prompt["type"], self.prompt["qid"]
        if pt == "quest_offer":
            if choice == "accept" and self.game:
                self.game.quest.start(qid)
        elif pt == "quest_done":
            if choice == "done" and self.game:
                self.game.quest.turn_in(qid)
        self.close()

    # ------------------------------------------------------------------
    def update(self, dt):
        pass


def quest_name(qid):
    from data.quests import get_quest
    q = get_quest(qid)
    return q["name"] if q else qid
