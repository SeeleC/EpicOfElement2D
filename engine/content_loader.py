# -*- coding: utf-8 -*-
"""JSON 内容加载器 (ContentLoader)。

作用：读取 content/ 目录下所有 *.json，把它们转换为 Registry 条目。

这对应前述「数据包 / 模组」思想 —— 引擎不写死内容，
而是把每个 JSON 文件当成一份「数据包」，解析并注册进日志。

约定的 JSON 结构（以物品为例）:
    {
      "category": "item",          // 分类，决定注册到哪个 Registry 分类
      "items": [                   // 数组，内含多条该分类条目
        {
          "id": "wood_sword",
          "name": "木制长剑",
          "type": "weapon",
          "quality": "common",
          "stats": { "attack": 5, "crit_rate": 0.02 },
          "hand": "main_hand",
          "desc": "新手探险者的第一把剑"
        }
      ]
    }

支持的文件分类 (category):
    item / class / skill / monster / npc / recipe /
    gather / equipment_set / trinket / quest / tile / biome / shop

每个文件可以包含一个或多个分类，同一个分类的条目可跨多个文件。
"""
import json
from pathlib import Path

from . import config
from .registry import Entry, REGISTRY

# 允许出现在 content JSON 顶层的分类字段
TOP_LEVEL_KEYS = {"category", "categories", "meta", "version", "lang"}

# 兜底策略：遇到未知分类也不至于崩溃，仅告警
_SAFE = True


class ContentLoadError(Exception):
    pass


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ContentLoadError(f"JSON 解析失败 {path.name}: {e}")
    except OSError as e:
        raise ContentLoadError(f"读取失败 {path}: {e}")


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _register_from_block(loader, category, block, source):
    """block 是某个分类下的具体条目 dict。"""
    content_id = str(block.get("id") or block.get("name") or "unnamed")
    namespace = str(block.get("namespace", "element"))
    fields = dict(block)
    # 剥离元字段，它们不进内容字典
    for meta_key in ("id", "namespace"):
        fields.pop(meta_key, None)
    entry = Entry(namespace, category, content_id, **fields)
    entry["source"] = source
    REGISTRY.register(entry)


def _register_category(loader, category, blocks, source):
    REGISTRY.note_source(category, source)
    for block in _ensure_list(blocks):
        _register_from_block(loader, category, block, source)


class ContentLoader:
    """负责装载 content/ 下所有 JSON 数据包。"""

    def __init__(self, content_dir=None):
        self.content_dir = Path(content_dir) if content_dir else config.CONTENT_DIR
        self.files_loaded = []
        self.error_log = []

    # ------------------------------------------------------------------
    # 顶层 API
    # ------------------------------------------------------------------
    def load_all(self):
        """装载 content 目录下全部 *.json。"""
        if not self.content_dir.exists():
            raise ContentLoadError(f"内容目录不存在: {self.content_dir}")
        for path in sorted(self.content_dir.glob("*.json")):
            self.load_file(path)
        return self

    def load_file(self, path):
        """装载单个 JSON 数据包文件。"""
        path = Path(path)
        data = _load_json(path)
        src = str(path)

        # 两种编写风格：
        #   风格A：顶层含 category 字段，直接给出一整格数组
        #   风格B：顶层多个分类字段，每个字段是数组
        cat_direct = data.get("category")
        if cat_direct:
            blocks = data.get(cat_direct) if cat_direct in data else data.get("entries")
            _register_category(self, str(cat_direct), blocks, src)
            self.files_loaded.append(path)
            return

        for key, value in data.items():
            if key in TOP_LEVEL_KEYS or key.startswith("_"):
                continue
            if isinstance(value, (dict, list)):
                _register_category(self, key, value, src)

        self.files_loaded.append(path)
        print(f"[Content] 装载 {path.name}")

    # ------------------------------------------------------------------
    # 校验 / 统计
    # ------------------------------------------------------------------
    def summary(self):
        s = REGISTRY.summarize()
        total = sum(s.values())
        return {"文件数": len(self.files_loaded), "条目总数": total, **s}

    # ---- README 一致性维护（数据驱动文档的自检） ----------------------
    # README.md 中记录一行「内容基线」标记，内容改动后此处会提醒同步文档，
    # 确保任何对 content / 玩法 / 操作 / 结构 的改动都能在 README 中反映。
    README_BASELINE_MARK = "CONTENT_BASELINE"

    def check_readme_sync(self, readme_path=None, verbose=True):
        """启动后比对 README 记录的内容基线与实际装载数，给出提醒。"""
        path = Path(readme_path) if readme_path else (config.ROOT_DIR / "README.md")
        if not path.exists():
            if verbose:
                print("[文档] ⚠️ 未找到 README.md，无法做内容基线校对。")
            return None
        baseline = self._read_baseline(path)
        actual = self.summary()["条目总数"]
        if baseline is None:
            return None
        if baseline != actual and verbose:
            print(f"[文档] 📘 README 内容基线过旧：记载 {baseline} 条，实际 {actual} 条。")
            print("[文档]    请更新 README 的介绍/教程/目录结构，并在注释标记中同步数量。")
            print(f"[文档]    补充方法：在 README 中更新 `<!-- {self.README_BASELINE_MARK}: <总数> -->`。")
        return baseline

    @staticmethod
    def _read_baseline(path):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if ContentLoader.README_BASELINE_MARK in line:
                    # 形如 <!-- CONTENT_BASELINE: 82 -->
                    token = line.split(":", 1)[-1]
                    digits = "".join(ch for ch in token if ch.isdigit())
                    return int(digits) if digits else None
        except OSError:
            return None
        return None

    def update_readme_baseline(self, readme_path=None):
        """把当前内容总数写回 README 的基线标记（手动刷新一次）。"""
        path = Path(readme_path) if readme_path else (config.ROOT_DIR / "README.md")
        if not path.exists():
            return False
        mark = f"<!-- {self.README_BASELINE_MARK}: {self.summary()['条目总数']} -->"
        text = path.read_text(encoding="utf-8")
        has = self.README_BASELINE_MARK in text
        if has:
            import re
            text = re.sub(r"<!--\s*CONTENT_BASELINE:\s*\d+\s*-->", mark, text)
        else:
            # 追加到标题下方
            text = text.replace("# ⚔️ 元素之诗：灾厄（Epic Of Elements 2D）\n",
                                "# ⚔️ 元素之诗：灾厄（Epic Of Elements 2D）\n\n> {mark}\n".format(mark=mark), 1)
        path.write_text(text, encoding="utf-8")
        return True


# 便捷：跨分类查询工具 -------------------------------------------------------
def parse_damage_array(entry, default_base=0.0):
    """解析技能里的 'damages': [130,143,...] 等级成长数组。"""
    arr = entry.get("damages") or entry.get("damage_per_level")
    if arr is None:
        return [default_base]
    return [float(v) for v in _ensure_list(arr)]


def resolve_id(entry, field, namespace="element", default=None):
    """把条目里引用的其它内容 id（如武器 id）解析为可用字符串。"""
    v = entry.get(field, default)
    if v is None:
        return default
    if isinstance(v, str) and ":" not in v:
        return f"{namespace}:{v}"
    return v


def load_all_content():
    """便利函数：一次性装载所有内容并返回 Registry 摘要。"""
    loader = ContentLoader()
    loader.load_all()
    return loader
