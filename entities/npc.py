# -*- coding: utf-8 -*-
"""
NPC 实体（npc.py）
==================
基于 data/npcs.py 生成，负责：
  - 待机上下浮动、名牌显示；
  - 与玩家的可交互范围判定（显示 E 提示）；
  - interact() 返回对话数据（对话系统后续读取）。
"""

import pygame

from config import make_font
from data.npcs import get_npc
from utils import draw_text


class NPC:
    def __init__(self, npc_id):
        d = get_npc(npc_id)
        if d is None:
            raise ValueError(f"未知NPC：{npc_id}")
        self.id = npc_id
        self.name = d["name"]
        self.role = d["role"]
        self.dialogues = d["dialogues"]
        self.shop = d["shop"]
        self.quests = d["quests"]
        self.color = d["color"]
        self.desc = d["desc"]
        self.sprite = d["sprite"]

        self.rect = pygame.Rect(int(d["pos"][0]), int(d["pos"][1]), 44, 64)
        self.bob = 0.0
        self.in_range = False

    def update(self, dt):
        self.bob += dt

    def in_range_of(self, player, max_dist=100):
        self.in_range = (
            abs(player.rect.centerx - self.rect.centerx) <= max_dist
            and abs(player.rect.centery - self.rect.centery) <= 70)
        return self.in_range

    def interact(self, player):
        """返回对话字典（对话系统后续读取）。"""
        return self.dialogues

    # ==================================================================
    def draw(self, surface, cam):
        sx, sy = cam.apply_point(self.rect.x, self.rect.y)
        bob = int(2 * (0.5 - abs((self.bob % 1.0) - 0.5) * 2))

        pygame.draw.ellipse(surface, (0, 0, 0, 90),
                            pygame.Rect(sx + 4, sy + 60, 36, 6))
        body = pygame.Rect(sx + 10, sy + 20 - bob, 24, 40)
        pygame.draw.rect(surface, (40, 40, 52), body)
        pygame.draw.rect(surface, self.color,
                         pygame.Rect(body.x + 3, body.y + 2,
                                     body.w - 6, body.h - 4))
        pygame.draw.circle(surface, (240, 205, 175), (sx + 22, sy + 10 - bob), 9)
        pygame.draw.circle(surface, (20, 20, 30), (sx + 24, sy + 9 - bob), 2)

        font = make_font(16)
        draw_text(surface, self.name, font, (240, 240, 240),
                  (sx + self.rect.w / 2, sy - 4), anchor="midbottom",
                  shadow=True)
        if self.in_range:
            draw_text(surface, "E", make_font(18, bold=True),
                      (255, 220, 80), (sx + self.rect.w / 2,
                                       sy + self.rect.h + 4), anchor="midtop")