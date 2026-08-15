# -*- coding: utf-8 -*-
"""内容注册表 (Registry)。

这是整个「数据驱动框架」的中枢：
所有由 content/*.json 定义的内容都会被解析为「内容条目(Entry)」并注册进来。

工作原理类似 MC 的 Registry：
    - 每个内容类型(item/class/skill/monster/...) 有独立的分类 (category)。
    - 每个条目有唯一的命名空间 id，形如 "element:wood_pickaxe"。
    - 通过 Registry.get(category, id) 快速取用。

这样 Python 引擎代码只依赖「条目字典」，从不写死具体内容，
从而支持任意扩展（加 JSON 即可加内容）。
"""
import json
from collections import defaultdict


class Entry(dict):
    """一条 JSON 内容定义。

    本质上是 dict 的轻量子类，附带便利方法与元信息。
    内容字段全部直接存储于 dict 键值中。
    """

    def __init__(self, namespace, content_type, content_id, **fields):
        super().__init__(fields)
        self.namespace = str(namespace)
        self.content_type = str(content_type)   # 如 'item'
        self.content_id = str(content_id)       # 如 'wood_pickaxe'
        self.__dict__["resource"] = f"{self.namespace}:{self.content_id}"

    # dict 的便利方法：让 __getattr__ 也能访问条目字段
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        # 元信息用普通属性，内容字段进 dict
        if name in ("namespace", "content_type", "content_id"):
            self.__dict__[name] = value
        else:
            self[name] = value

    def get(self, key, default=None):
        return dict.get(self, key, default)

    def qualified_id(self):
        return f"{self.namespace}:{self.content_id}"

    def __repr__(self):
        return f"<Entry {self.qualified_id()} type={self.content_type}>"


class Registry:
    """内容注册表：按分类存放所有条目。"""

    def __init__(self):
        # category -> {qualified_id -> Entry}
        self._by_category = defaultdict(dict)
        # qualified_id -> Entry （全局扁平索引）
        self._all = {}
        # 记录的「加载来源文件」，便于调试与重载
        self._sources = {}

    # ------------------------------------------------------------------
    # 注册
    # ------------------------------------------------------------------
    def register(self, entry):
        qid = entry.qualified_id()
        self._by_category[entry.content_type][qid] = entry
        self._all[qid] = entry

    def register_dict(self, content_type, namespace, content_id, fields):
        entry = Entry(namespace, content_type, content_id, **fields)
        self.register(entry)
        return entry

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def get(self, content_type, content_id, namespace="element", default=None):
        """取一个条目。可通过裸 id 或 qualified id 查询。"""
        qid = content_id if ":" in str(content_id) else f"{namespace}:{content_id}"
        return self._by_category.get(content_type, {}).get(qid, default)

    def all_of(self, content_type):
        """返回某分类所有条目（value 列表）。"""
        return list(self._by_category.get(content_type, {}).values())

    def by_qualified(self, qid, default=None):
        return self._all.get(qid, default)

    def categories(self):
        return list(self._by_category.keys())

    # ------------------------------------------------------------------
    # 源追踪 / 序列化
    # ------------------------------------------------------------------
    def note_source(self, content_type, filepath):
        self._sources[content_type] = str(filepath)

    def source_of(self, content_type):
        return self._sources.get(content_type)

    def summarize(self):
        """返回形如 {分类: 条目数} 的摘要，便于启动时打印。"""
        return {cat: len(ents) for cat, ents in self._by_category.items()}


# 全局单例
REGISTRY = Registry()
