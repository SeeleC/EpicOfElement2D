# -*- coding: utf-8 -*-
"""
任务系统（quest.py）
====================
主线 + 支线任务的进度管理：
  - 接取 / 追踪 / 交付 / 自动衔接下一主线
  - 由事件驱动推进：on_kill / on_collect / on_talk / on_level / on_clear_dungeon
  - 交付时发放奖励（经验 / 金币 / 物品）
"""

from data.quests import get_quest
from data.npcs import get_npc


class QuestSystem:
    def __init__(self, player, game=None):
        self.player = player
        self.game = game
        if not hasattr(player, "quests"):
            player.quests = {}
        if not hasattr(player, "quest_progress"):
            player.quest_progress = {}

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def available(self, npc_id):
        """NPC 可接取的任务。"""
        npc = get_npc(npc_id)
        if not npc:
            return []
        out = []
        for qid in npc["quests"]:
            q = get_quest(qid)
            if not q:
                continue
            if qid in self.player.quests:
                continue
            if self.player.level < q["level"]:
                continue
            out.append(q)
        return out

    def is_active(self, qid):
        return self.player.quests.get(qid) == "active"

    def is_completed(self, qid):
        return self.player.quests.get(qid) == "completed"

    def is_completable(self, qid):
        if not self.is_active(qid):
            return False
        q = get_quest(qid)
        prog = self.player.quest_progress.get(qid, [])
        return all(self._obj_done(o, p)
                   for o, p in zip(q["objectives"], prog))

    def active_quests(self):
        return [get_quest(qid) for qid, st in self.player.quests.items()
                if st == "active"]

    def _obj_done(self, obj, progress):
        return progress >= obj.get("count", 1)

    # ------------------------------------------------------------------
    # 接取 / 推进
    # ------------------------------------------------------------------
    def start(self, qid):
        if qid in self.player.quests:
            return False
        q = get_quest(qid)
        if not q or self.player.level < q["level"]:
            return False
        self.player.quests[qid] = "active"
        self.player.quest_progress[qid] = [0] * len(q["objectives"])
        self._notify(f"接受任务：{q['name']}")
        return True

    def _advance(self, qid, idx, amount=1):
        q = get_quest(qid)
        if not q or not self.is_active(qid):
            return
        prog = self.player.quest_progress[qid]
        prog[idx] = min(q["objectives"][idx].get("count", 1),
                        prog[idx] + amount)
        if self.is_completable(qid):
            self._notify(f"任务完成！返回 {q['giver']} 处交付：{q['name']}")

    # ------------------------------------------------------------------
    # 事件驱动
    # ------------------------------------------------------------------
    def _for_each_objective(self, qtype, match_key, match_val, amount=1):
        for qid in list(self.player.quests.keys()):
            if not self.is_active(qid):
                continue
            q = get_quest(qid)
            if not q:
                continue
            for i, obj in enumerate(q["objectives"]):
                if obj["type"] == qtype and obj.get(match_key) == match_val:
                    self._advance(qid, i, amount)

    def on_kill(self, monster_id):
        self._for_each_objective("kill", "target", monster_id)

    def on_collect(self, item_id, amount=1):
        self._for_each_objective("collect", "target", item_id, amount)

    def on_talk(self, npc_id):
        self._for_each_objective("talk", "target", npc_id)

    def on_level(self, level):
        self._for_each_objective("reach_level", "level", level)

    def on_clear_dungeon(self, map_id):
        self._for_each_objective("clear_dungeon", "target", map_id)

    # ------------------------------------------------------------------
    # 交付
    # ------------------------------------------------------------------
    def turn_in(self, qid):
        if not self.is_completable(qid):
            return False
        q = get_quest(qid)
        self.player.quests[qid] = "completed"
        self._grant_rewards(q)
        if q.get("next"):
            self.start(q["next"])
        self._notify(f"任务完成：{q['name']}")
        return True

    def _grant_rewards(self, q):
        r = q["rewards"]
        self.player.gain_exp(r.get("exp", 0))
        self.player.gold += r.get("gold", 0)
        inv = self.game.inv if self.game else None
        for item_id, count in r.get("items", []):
            if inv:
                got = inv.add(item_id, count)
                if got < count:
                    self._notify(f"背包不足，{get_item(item_id)['name']} x{count - got} 未获得")

    def _notify(self, msg):
        if self.game and hasattr(self.game, "notify"):
            self.game.notify(msg)


def get_item(item_id):
    from data.items import get_item as _gi
    return _gi(item_id)