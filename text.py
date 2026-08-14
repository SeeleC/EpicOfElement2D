# -*- coding: utf-8 -*-
"""
现代化文本引擎（text.py）
=========================
统一文本渲染管线，全项目文本自动获得抗锯齿：

  后端优先级：
    1) pygame.freetype —— FreeType 渲染器：真抗锯齿 + 字距(kerning)
    2) pygame.font    —— 内置 AA 渲染 + 2x 平滑超采样兜底

  - 字形/像素缓存（LRU 上限），避免重复渲染
  - draw_text() 与旧 utils.draw_text 签名完全兼容，调用点零改动
"""

import pygame

_fallback_names = ["microsoftyahei", "msyh", "pingfang", "simhei",
                   "notosanscjk", "wenquanyimicrohei", "arial"]

try:
    import pygame.freetype as _ft
    _HAS_FT = True
except Exception:
    _HAS_FT = False

try:
    from config import FONT_PATH          # 建议指向中文字体，如 assets/fonts/msyh.ttc
except Exception:
    FONT_PATH = None

AA_SCALE = 2            # 超采样倍率（>1 更柔和；1 关闭）
_CACHE = {}
_CACHE_MAX = 1200
_FT_FONTS = {}
_PG_FONTS = {}


# ------------------------------------------------------------------ 字体
def _get_ft_font(size, bold=False):
    key = (size, bold)
    f = _FT_FONTS.get(key)
    if f is None and _HAS_FT:
        try:
            f = _ft.Font(FONT_PATH, size)
        except Exception:
            f = _ft.SysFont(_fallback_names, size)
        f.kerning = True                    # 开启自动字距
        _FT_FONTS[key] = f
    return f


def _get_pg_font(size, bold=False):
    key = (size, bold)
    f = _PG_FONTS.get(key)
    if f is None:
        try:
            f = pygame.font.Font(FONT_PATH, size)
        except Exception:
            f = pygame.font.SysFont(_fallback_names, size)
        f.set_bold(bold)
        _PG_FONTS[key] = f
    return f


def _font_size(font):
    """从字体对象解析字号（优先 config 注册表，其次估算）。"""
    if isinstance(font, int):
        return font
    try:
        import config
        reg = getattr(config, "_FONT_SIZES", {})
        s = reg.get(id(font))
        if s:
            return s
    except Exception:
        pass
    return max(8, int(font.get_height() * 1.25))


def _font_bold(font):
    if isinstance(font, int):
        return False
    try:
        return bool(font.get_bold())
    except Exception:
        return False


# ------------------------------------------------------------------ 渲染
def _render_ft(text, size, color, bold):
    f = _get_ft_font(size * AA_SCALE if AA_SCALE > 1 else size, bold)
    if f is None:
        return _render_pg(text, size, color, bold)
    surf, _r = f.render(text, fgcolor=color)      # freetype 自带 AA
    if AA_SCALE > 1:
        w = max(1, surf.get_width() // AA_SCALE)
        h = max(1, surf.get_height() // AA_SCALE)
        surf = pygame.transform.smoothscale(surf, (w, h))
    return surf


def _render_pg(text, size, color, bold):
    f = _get_pg_font(size * AA_SCALE if AA_SCALE > 1 else size, bold)
    surf = f.render(text, True, color)            # True = 抗锯齿
    if AA_SCALE > 1:
        w = max(1, surf.get_width() // AA_SCALE)
        h = max(1, surf.get_height() // AA_SCALE)
        surf = pygame.transform.smoothscale(surf, (w, h))
    return surf


def _render_aliased(text, size, color, bold):
    """aa=False 时：无抗锯齿、不超采样。"""
    f = _get_pg_font(size, bold)
    return f.render(text, False, color)


def _cached(text, size, color, bold, backend):
    key = (text, size, color, bold, backend)
    surf = _CACHE.get(key)
    if surf is None:
        surf = _render_ft(text, size, color, bold) if backend == "ft" \
            else _render_pg(text, size, color, bold)
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.clear()
        _CACHE[key] = surf
    return surf


# ------------------------------------------------------------------ 布局
def _anchor_rect(surf, pos, anchor, off):
    x, y = int(pos[0]) + off[0], int(pos[1]) + off[1]
    if anchor == "center":
        return (x - surf.get_width() // 2, y - surf.get_height() // 2)
    if anchor == "topleft":
        return (x, y)
    if anchor == "topright":
        return (x - surf.get_width(), y)
    if anchor == "midleft":
        return (x, y - surf.get_height() // 2)
    if anchor == "midright":
        return (x - surf.get_width(), y - surf.get_height() // 2)
    if anchor == "midtop":
        return (x - surf.get_width() // 2, y)
    if anchor == "midbottom":
        return (x - surf.get_width() // 2, y - surf.get_height())
    if anchor == "bottomleft":
        return (x, y - surf.get_height())
    if anchor == "bottomright":
        return (x - surf.get_width(), y - surf.get_height())
    return (x, y)


# ------------------------------------------------------------------ 对外接口
def draw_text(surface, text, font, color, pos, anchor="topleft",
              shadow=False, alpha=255, aa=True):
    """绘制（抗锯齿）文本。font 可为 pygame.font.Font 或 int 字号。"""
    if text is None or text == "":
        return
    text = str(text)
    size = _font_size(font)
    bold = _font_bold(font)
    backend = "ft" if (_HAS_FT and aa) else "pg"

    if aa:
        surf = _cached(text, size, color, bold, backend)
    else:
        surf = _render_aliased(text, size, color, bold)

    if alpha < 255:
        surf = surf.copy()
        surf.fill((255, 255, 255, alpha),
                  special_flags=pygame.BLEND_RGBA_MULT)

    if shadow:
        sh = _cached(text, size, (0, 0, 0), bold, backend) if aa \
            else _render_aliased(text, size, (0, 0, 0), bold)
        surface.blit(sh, _anchor_rect(sh, pos, anchor, (2, 2)))

    surface.blit(surf, _anchor_rect(surf, pos, anchor, (0, 0)))
    return surf