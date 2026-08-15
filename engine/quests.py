# -*- coding: utf-8 -*-
"""任务系统：进度追踪、目标完成、奖励发放。

任务定义来自 quest.json，目标类型支持 kill / gather / talk。
"""
from .registry import REGISTRY


class QuestState:
    def __init__(self, quest_id, progress=None):
        self.quest_id = quest_id
        self.base = REGISTRY.get("quest", quest_id) or {}
        # progress: 目标类型 -> 已达成次数
        self.progress = progress or {}

    @property
    def name(self):
        return self.base.get("name", self.quest_id)

    @property
    def complete(self):
        obj = self.base.get("objectives", [])
        for o in obj:
            key = o.get("type")
            cnt = o.get("count", 1)
            cur = self.progress.get(key, 0)
            if cur < cnt:
                # 多目标同一类型时分别追踪 target
                tcur = self.progress.get(f"{key}:{o.get('target')}", cur)
                if tcur < cnt:
                    return False
        return True

    def record(self, etype, target=None):
        key = etype
        if target:
            tkey = f"{etype}:{target}"
            self.progress[tkey] = self.progress.get(tkey, 0) + 1
        else:
            self.progress[key] = self.progress.get(key, 0) + 1
        return self.complete

    def objective_text(self):
        lines = []
        for o in self.base.get("objectives", []):
            key = o.get("type")
            tcur = self.progress.get(f"{key}:{o.get('target')}", 0)
            lines.append(f"- {o.get('desc', o.get('type'))} {tcur}/{o.get('count', 1)}")
        return "\n".join(lines)


class QuestManager:
    def __init__(self, player):
        self.player = player
        self.active = {}       # quest_id -> QuestState
        self.completed = set()

    def load_progress(self, quests):
        self.active = {qid: QuestState(qid, data) for qid, data in quests.items()}

    def accept(self, quest_id):
        if quest_id in self.active or quest_id in self.completed:
            return
        self.active[quest_id] = QuestState(quest_id)
        self.player.quests[quest_id] = self.active[quest_id].progress
        return self.active[quest_id]

    def record_quests(self, etype, target=None):
        done = []
        for qid, qs in list(self.active.items()):
            if qs.record(etype, target):
                self.complete(qid)
                done.append(qid)
        return done

    def complete(self, quest_id):
        qs = self.active.pop(quest_id, None)
        if not qs:
            return None
        base = qs.base
        rewards = base.get("rewards", {})
        self.player.inventory.gold += rewards.get("gold", 0)
        self.player.add_exp(rewards.get("exp", 0))
        for it in rewards.get("items", []):
            self.player.inventory.add(it["id"], it.get("count", 1))
        self.completed.add(quest_id)
        self.player.quests.pop(quest_id, None)
        return rewards
