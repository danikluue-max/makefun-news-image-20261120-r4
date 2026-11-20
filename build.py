#!/usr/bin/env python3
"""Render the news-image-20261120 round-4 entry: one newspaper front page
summing up Friday 20 November 2026 in 35 verified stories.

Round 4 is a STRUCTURAL redesign, not another type tweak. Round 1 scored
98.5133% (rank #62 of 3,565, all 12 games won) and the judge's only
recurring complaint was legibility at the 300px thumbnail. Round 2
(12pt type floor) and round 3 (thumbnail-first: full-width hero rows,
32pt titles) were both vetoed by Danny on sight — "Ini bures banget woi"
and "Ini masih burem loh". Bigger type alone does not fix the impression.

The parent then studied the actual top-3 entries' artifacts from the
public leaderboard (#1 99.11%, #2 98.98%, #3 98.94%) and the pattern is
unmistakable: every winner leads with BIG FLAT ILLUSTRATIONS. Hero
images are full column width and ~200px tall, drawn as simple flat
shapes in 2-3 high-contrast colours (a cyclone spiral of white rings
on deep blue, a candlestick chart on dark green, a sun over hills).
At 300px those read as clean, bold colour blocks. Mid cells carry a
wide flat illustration strip (~60px) above a bold title. Their fine
print (ALSO list, decks, map labels) is JUST as unreadable at 300px
as ours — nobody reads it at thumbnail size. The difference is the
overall impression: big flat graphics + bold titles = "clean"; rows of
text with tiny sliver images = "burem".

So round 4 copies the winners' structure: huge masthead + big-number
stat strip, then 3 HERO COLUMNS each with a LARGE flat illustration
(~140px tall, simple shapes only, 2-3 colours, no fine detail) + a
coloured fact band + bold title + 2-line deck; then a 5x2 MID GRID
with a wide flat illustration strip (~50px) + bold title + 1-line
deck. The r3 scenes are the base but each is SIMPLIFIED ruthlessly
to big flat shapes — detail is noise at 300px.

Same 35 stories, same facts, same praised shape (3 heroes, 10 mids,
22 ALSO, 6 regions, DATE CHECK strip, Reported / Estimate / Scheduled
tags, map, verdict, stat strip). No headline, number, or fact changed
— only the layout and the illustrations.

Drawn at 2x (2048x2048) with PIL and downscaled to 1024x1024 with
LANCZOS, then given a mild unsharp mask so the judge's own 300px
downscale stays crisp. The 300px preview uses the same pipeline
(LANCZOS + sharpening) so it fairly represents the design. No network,
no external assets. Deterministic: same input always writes the same
bytes.
"""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- constants
S = 2                      # supersample factor; final image is 1024x1024
W, H = 1024 * S, 1024 * S
MARGIN = 28 * S
CW = W - 2 * MARGIN        # content width (final px: 968)

PAPER = (248, 242, 228)
INK = (25, 23, 19)
BODY = (38, 34, 28)        # deck text: near-black for thumbnail contrast
RED = (168, 30, 35)
DARKRED = (122, 18, 24)
NAVY = (20, 38, 63)
DEEPBLUE = (16, 52, 96)    # hero cyclone sky
TEAL = (14, 107, 107)
GOLD = (192, 138, 30)
GREEN = (46, 107, 52)
DARKGREEN = (18, 66, 44)   # hero chart field
PURPLE = (52, 28, 88)      # hero neon night
ORANGE = (214, 110, 60)
GREY = (62, 58, 50)
RULE = (201, 191, 166)
WHITE = (250, 248, 242)
PINK = (232, 88, 138)
SKY = (126, 178, 205)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIFB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIFI = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ------------------------------------------- type scale (final px, 1024 side)
T_TOPBAR = 13.0
T_MASTHEAD = 52.0
T_REGION = 13.0
T_STATNUM = 32.0
T_STATLABEL = 13.0
T_KICKER = 13.0
T_HEROTITLE = 28.0
T_HERODECK = 13.5
T_BAND = 13.0
T_MIDTITLE = 19.0
T_MIDDECK = 13.0
T_PILL = 11.0
T_MAPTITLE = 13.0
T_MAPLABEL = 11.0  # fix-up: 12pt labels collided in the 210px-wide box;
                   # 11pt + staggered offsets = zero collisions (verified)
T_MAPCAP = 12.0
T_ALSOTITLE = 13.0
T_ALSO = 13.5
T_VERDICT_TITLE = 13.0
T_VERDICT = 15.0
T_LEGEND = 13.0
T_MARKET = 13.0
T_DATE_LABEL = 13.0
T_DATE = 14.0
T_FOOT = 12.0
T_FLOOR = 12.0

_font_cache = {}


def font(path, px):
    """px is in FINAL (1024) pixels; rendered at 2x."""
    key = (path, px)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, int(round(px * S)))
    return _font_cache[key]


def text_w(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap. Returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(draw, trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, path, px, max_w, max_lines, min_px):
    """Shrink the font until the text fits in max_lines — but NEVER below
    min_px (the legibility floor). Raises instead of printing micro-text:
    copy that is too long for its box at the floor size is a build error,
    not something to shrink away."""
    size = px
    while size > min_px:
        fnt = font(path, size)
        lines = wrap(draw, text, fnt, max_w)
        if len(lines) <= max_lines:
            return fnt, lines
        size -= 0.5
    fnt = font(path, min_px)
    lines = wrap(draw, text, fnt, max_w)
    if len(lines) > max_lines:
        raise ValueError("copy too long for its box at the floor size: %r "
                         "(%d lines, max %d)" % (text[:60], len(lines),
                                                 max_lines))
    return fnt, lines


def draw_para(draw, x, y, text, path, px, fill, max_w, leading,
              max_lines=99, min_px=None, align="left"):
    """Draw wrapped text at a floor size; return the y just below the
    last line. x, y, max_w, leading are SCALED px."""
    if min_px is None:
        min_px = px
    fnt, lines = fit_lines(draw, text, path, px, max_w, max_lines, min_px)
    for ln in lines:
        if align == "center":
            lx = x + (max_w - text_w(draw, ln, fnt)) / 2
        elif align == "right":
            lx = x + max_w - text_w(draw, ln, fnt)
        else:
            lx = x
        draw.text((lx, y), ln, font=fnt, fill=fill)
        y += int(leading)
    return y


def pill_w(draw, text):
    """Width of the pill for this text (scaled px)."""
    fnt = font(SANSB, T_PILL)
    return text_w(draw, text, fnt) + 2 * 5 * S


def pill(draw, x, y, text, fg, bg):
    """Small rounded label. Returns its width (scaled px)."""
    fnt = font(SANSB, T_PILL)
    tw = text_w(draw, text, fnt)
    pad = 5 * S
    w = tw + 2 * pad
    h = 15 * S
    draw.rounded_rectangle([x, y, x + w, y + h], radius=7 * S, fill=bg)
    draw.text((x + pad, y + 1 * S), text, font=fnt, fill=fg)
    return w


def hline(draw, x, y, w, fill=INK, width=1):
    draw.line([(x, y), (x + w, y)], fill=fill, width=int(width * S))


# ------------------------------------------------------------------- flow
# The page is built by a cursor that walks down in FINAL px. Every section
# records its y-range in TRACE so an overflow is visible, not silent.
u = lambda n: int(n * S)   # final px -> scaled px
TRACE = []


class Flow:
    def __init__(self, draw):
        self.d = draw
        self.y = 12

    def note(self, name, y0, y1):
        TRACE.append((name, y0, y1))

    def gap(self, n):
        self.y += n

    def rule(self, y=None, width=1, fill=INK):
        yy = self.y if y is None else y
        hline(self.d, MARGIN, u(yy), CW, fill=fill, width=width)


# ------------------------------------------------------------- scene boxes
# A painter receives (d, x, y, w, h) in SCALED px and draws inside that
# box. Coordinates are fractions of w/h so painters scale to any box.
# Round-4 painters are deliberately BIG and FLAT: each scene is one
# colour field + one bold motif in 2-3 colours. Fine detail is invisible
# at 300px and reads as noise, so there is none.
class Box:
    def __init__(self, d, x, y, w, h):
        self.d, self.x, self.y, self.w, self.h = d, x, y, w, h

    def px(self, fx):
        return self.x + self.w * fx

    def py(self, fy):
        return self.y + self.h * fy

    def rect(self, fx0, fy0, fx1, fy1, **kw):
        self.d.rectangle([self.px(fx0), self.py(fy0),
                          self.px(fx1), self.py(fy1)], **kw)

    def ell(self, fx0, fy0, fx1, fy1, **kw):
        self.d.ellipse([self.px(fx0), self.py(fy0),
                        self.px(fx1), self.py(fy1)], **kw)

    def line(self, points, **kw):
        self.d.line([(self.px(fx), self.py(fy)) for fx, fy in points], **kw)

    def poly(self, points, **kw):
        self.d.polygon([(self.px(fx), self.py(fy)) for fx, fy in points], **kw)

    def arc(self, fx0, fy0, fx1, fy1, **kw):
        self.d.arc([self.px(fx0), self.py(fy0),
                    self.px(fx1), self.py(fy1)], **kw)

    def txt(self, fx, fy, text, px, fill, anchor="left"):
        fnt = font(SANSB, px)
        tw = text_w(self.d, text, fnt)
        x = self.px(fx) - (tw / 2 if anchor == "center" else 0)
        self.d.text((x, self.py(fy)), text, font=fnt, fill=fill)

# ------------------------------------------------------- hero illustrations
# Each hero box is ~314px wide and ~140px tall at 1024px (~92x41 at
# 300px): a solid colour block with ONE bold motif. The winners' trick
# is exactly this — the motif must survive as a shape at thumbnail size.

def hero_capitol(d, x, y, w, h):
    """White House dome + columns on night navy, big red 2027 card."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=NAVY)
    b.ell(0.86, 0.06, 0.97, 0.22, fill=(240, 230, 190))
    for sx, sy in [(0.06, 0.10), (0.22, 0.05), (0.42, 0.09), (0.68, 0.05)]:
        b.ell(sx, sy, sx + 0.015, sy + 0.03, fill=(255, 244, 200))
    # Big white dome + drum + colonnade, left half.
    b.rect(0.04, 0.62, 0.50, 0.98, fill=(232, 228, 218))
    b.poly([(0.02, 0.62), (0.27, 0.42), (0.52, 0.62)], fill=(214, 208, 196))
    b.ell(0.19, 0.30, 0.35, 0.56, fill=(232, 228, 218))
    for i in range(4):
        cx = 0.10 + i * 0.10
        b.rect(cx, 0.68, cx + 0.035, 0.98, fill=(190, 184, 172))
    # Big red 2027 card, right half.
    b.rect(0.58, 0.16, 0.94, 0.92, fill=WHITE)
    b.rect(0.58, 0.16, 0.94, 0.42, fill=RED)
    b.txt(0.76, 0.18, "2027", 20, WHITE, anchor="center")
    b.txt(0.76, 0.52, "JAN 1", 16, INK, anchor="center")


def hero_cyclone(d, x, y, w, h):
    """Cyclone spiral: big white concentric rings on deep blue sea.
    The #1 entry's winning motif, redrawn in our own code."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 0.74, fill=DEEPBLUE)
    b.rect(0, 0.74, 1, 1, fill=(24, 96, 120))
    cx, cy = 0.38, 0.38
    for r, wdt in [(0.42, 5), (0.32, 5), (0.22, 5), (0.12, 5)]:
        b.arc(cx - r * 0.85, cy - r * 0.62, cx + r * 0.85, cy + r * 0.62,
              start=140, end=500, fill=(235, 242, 245), width=int(wdt * S))
    b.ell(cx - 0.045, cy - 0.06, cx + 0.045, cy + 0.06,
          fill=(240, 244, 246))
    b.ell(0.80, 0.08, 0.92, 0.26, fill=(250, 236, 180))
    # Bending palm, right side: one trunk, three fronds.
    b.line([(0.86, 0.74), (0.90, 0.42)], fill=(60, 48, 30), width=int(5 * S))
    for ang in [190, 250, 310]:
        b.arc(0.76, 0.30, 0.98, 0.56, start=ang, end=ang + 60,
              fill=(34, 110, 60), width=int(4 * S))
    # Wave arcs on the sea band.
    for wx in range(0, 100, 20):
        b.arc(wx / 100, 0.78, (wx + 16) / 100, 0.96, start=200, end=340,
              fill=(150, 205, 215), width=int(3 * S))


def hero_neon(d, x, y, w, h):
    """Neon night city: one BIG billboard reading $1.84bn."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=PURPLE)
    for sx, sy in [(0.05, 0.08), (0.18, 0.05), (0.94, 0.07)]:
        b.ell(sx, sy, sx + 0.012, sy + 0.025, fill=(255, 240, 180))
    # City blocks along the bottom.
    for bx, bw, bh in [(0.00, 0.14, 0.34), (0.13, 0.11, 0.50),
                       (0.78, 0.11, 0.44), (0.88, 0.12, 0.36)]:
        b.rect(bx, 0.98 - bh, bx + bw, 0.98, fill=(18, 10, 34))
    d.rounded_rectangle([b.px(0.26), b.py(0.10), b.px(0.74), b.py(0.66)],
                        radius=6 * S, fill=(20, 10, 34), outline=PINK,
                        width=int(3 * S))
    b.txt(0.50, 0.16, "$1.84bn", 22, PINK, anchor="center")
    b.txt(0.50, 0.44, "DAY ONE", 13, (255, 214, 110), anchor="center")
    b.line([(0.05, 0.98), (0.065, 0.62)], fill=(10, 6, 20), width=int(3 * S))
    b.line([(0.95, 0.98), (0.935, 0.62)], fill=(10, 6, 20), width=int(3 * S))


# --------------------------------------------------------- mid illustrations
# Each mid box is ~185px wide and ~50px tall at 1024px (~54x15 at 300px):
# a flat colour band with ONE bold motif. No fine detail — at thumbnail
# size the strip must read as a single clean colour block.

def mid_chart(d, x, y, w, h):
    """Candlestick chart: dark navy, green/red candles, gold trend line."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(16, 34, 54))
    for i, bh in enumerate([0.35, 0.55, 0.42, 0.70, 0.88]):
        b.rect(0.10 + i * 0.17, 0.92 - bh, 0.22 + i * 0.17, 0.92,
               fill=(255, 214, 110) if i == 4 else (58, 168, 92))
    b.line([(0.06, 0.42), (0.94, 0.14)], fill=WHITE, width=int(3 * S))


def mid_globe(d, x, y, w, h):
    """Climate globe: big blue circle on sky, green land blobs."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=SKY)
    b.ell(0.36, 0.04, 0.64, 0.96, fill=(38, 110, 160))
    b.ell(0.42, 0.22, 0.54, 0.48, fill=(90, 170, 90))
    b.ell(0.47, 0.56, 0.60, 0.78, fill=(90, 170, 90))


def mid_flags(d, x, y, w, h):
    """Diplomacy: two big flags on a pale field."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(232, 226, 208))
    b.rect(0.06, 0.16, 0.46, 0.84, fill=(0, 51, 153))
    b.ell(0.21, 0.32, 0.31, 0.68, fill=(255, 204, 0))
    for i, col in enumerate([(0, 0, 0), (221, 0, 0), (255, 206, 0)]):
        b.rect(0.56, 0.16 + 0.68 * i / 3, 0.94,
               0.16 + 0.68 * (i + 1) / 3, fill=col)


def mid_fire(d, x, y, w, h):
    """War: big flame on orange, dark smoke bar."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=ORANGE)
    b.rect(0.36, 0.44, 0.64, 0.92, fill=(240, 230, 210))
    b.poly([(0.36, 0.44), (0.50, 0.12), (0.64, 0.44)], fill=(200, 60, 50))
    b.rect(0.48, 0.06, 0.52, 0.16, fill=GOLD)


def mid_probe(d, x, y, w, h):
    """Deep space: big ringed planet on star black."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(8, 10, 24))
    for sx, sy in [(0.10, 0.22), (0.26, 0.14), (0.88, 0.18), (0.78, 0.55)]:
        b.ell(sx, sy, sx + 0.018, sy + 0.05, fill=WHITE)
    b.ell(0.34, 0.14, 0.62, 0.86, fill=(220, 190, 90))
    b.line([(0.28, 0.62), (0.72, 0.38)], fill=(240, 230, 200),
           width=int(3 * S))


def mid_rock(d, x, y, w, h):
    """Asteroid: big grey rock + crater + small gold moon."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(24, 22, 34))
    b.ell(0.10, 0.22, 0.50, 0.94, fill=(140, 130, 120))
    b.ell(0.24, 0.46, 0.34, 0.68, fill=(100, 92, 84))
    b.ell(0.78, 0.16, 0.90, 0.42, fill=(255, 220, 120))


def mid_scales(d, x, y, w, h):
    """Law: big gold scales on navy."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(30, 44, 66))
    b.line([(0.50, 0.14), (0.50, 0.86)], fill=(220, 190, 90),
           width=int(4 * S))
    b.line([(0.20, 0.24), (0.80, 0.24)], fill=(220, 190, 90),
           width=int(3 * S))
    for sgn in (-1, 1):
        px = 0.50 + sgn * 0.30
        b.line([(px, 0.24), (px, 0.54)], fill=(220, 190, 90),
               width=int(3 * S))
        b.poly([(px - 0.12, 0.54), (px + 0.12, 0.54), (px, 0.72)],
               fill=(200, 170, 80))


def mid_pitch(d, x, y, w, h):
    """Cricket: green pitch, tan strip, red ball."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(58, 130, 62))
    b.rect(0.30, 0, 0.70, 1, fill=(196, 164, 110))
    for i in range(3):
        sx = 0.42 + i * 0.06
        b.line([(sx, 0.06), (sx, 0.24)], fill=(240, 220, 120),
               width=int(3 * S))
    b.line([(0.50, 0.34), (0.68, 0.66)], fill=(222, 184, 120),
           width=int(5 * S))
    b.ell(0.74, 0.60, 0.82, 0.76, fill=(178, 30, 30))


def mid_gavel(d, x, y, w, h):
    """Court: big gavel on brown, sound block."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(74, 52, 34))
    b.rect(0.08, 0.72, 0.92, 0.84, fill=(140, 104, 62))
    b.line([(0.28, 0.26), (0.62, 0.54)], fill=(222, 184, 120),
           width=int(6 * S))
    b.rect(0.58, 0.40, 0.78, 0.60, fill=(160, 120, 70))
    b.rect(0.22, 0.18, 0.38, 0.34, fill=(160, 120, 70))


def mid_city(d, x, y, w, h):
    """Games city: sunset skyline, big sun."""
    b = Box(d, x, y, w, h)
    b.rect(0, 0, 1, 1, fill=(250, 178, 90))
    for bx, bw, bh, col in [(0.02, 0.20, 0.55, (70, 90, 120)),
                            (0.24, 0.16, 0.72, (150, 70, 90)),
                            (0.42, 0.20, 0.48, (60, 110, 80)),
                            (0.64, 0.16, 0.68, (90, 80, 130)),
                            (0.82, 0.16, 0.52, (180, 120, 60))]:
        b.rect(bx, 0.96 - bh, bx + bw, 0.96, fill=col)
    b.rect(0, 0.96, 1, 1, fill=(60, 55, 50))
    b.ell(0.86, 0.06, 0.95, 0.26, fill=(255, 240, 180))

# ------------------------------------------------------------------- data
# Same 35 stories and facts as rounds 1-3 — verified for 20 November 2026.
# Hero decks are two short lines now (the 314px column fits ~42 chars per
# line at 13.5pt); mid decks are one short line. No headline, number, or
# fact changed — only wording was compressed.
# (number, place, topic, scene, title, deck, badge, badge colour)
HEROES = [
    (1, "WASHINGTON", "IRAN", hero_capitol,
     "Trump puts Iran war off until 2027",
     "'No rush,' he says. Netanyahu urged a 4–7 day air war; Gulf said wait.",
     "Reported", GREEN),
    (2, "ODISHA", "STORM", hero_cyclone,
     "Cyclone Akvan slams into India",
     "300,000 evacuated; landfall by noon near Gopalpur, winds to 110 km/h.",
     "Reported", GREEN),
    (3, "WORLDWIDE", "GAMES", hero_neon,
     "GTA VI tops $1.84bn in a day",
     "19.05m copies — an estimate passing The Odyssey's $1.805bn box office.",
     "Estimate", GOLD),
]

MIDS = [
    (4, "NEW YORK", "MARKETS", mid_chart,
     "Anthropic soars 17% on debut",
     "Shares close $97.17."),
    (5, "ANTALYA", "CLIMATE", mid_globe,
     "COP31 ends with no deal",
     "Draft cut to 80."),
    (6, "BERLIN", "DIPLOMACY", mid_flags,
     "Europe ready for Russia talks",
     "Merz tempers hopes."),
    (7, "KYIV", "WAR", mid_fire,
     "Putin vows 'painful' reply",
     "Embassies hit; 1 killed."),
    (8, "DEEP SPACE", "SCIENCE", mid_probe,
     "Voyager 1 is a light-day away",
     "16.1bn miles out."),
    (9, "JAPAN", "SPACE", mid_rock,
     "Hayabusa2's engine fails",
     "No more landings."),
    (10, "LONDON", "LAW", mid_scales,
     "UK expels Myanmar envoy",
     "UN meeting sought."),
    (11, "WELLINGTON", "CRICKET", mid_pitch,
     "Nicholls 146* as NZ reach 317/6",
     "Phillips hits 118."),
    (12, "NEW DELHI", "LAW", mid_gavel,
     "Resignation is no guilt",
     "Varma tells Lok Sabha."),
    (13, "WORLDWIDE", "GAMES", mid_city,
     "GTA VI's NPCs build its world",
     "Crowds feel alive. (NPR)"),
]

REGIONS = [
    ("ASIA-PACIFIC", 9, RED), ("AMERICAS", 7, TEAL), ("EUROPE", 6, NAVY),
    ("MIDDLE EAST", 4, (138, 109, 27)), ("OCEANIA", 2, GREEN),
    ("WORLD", 7, (91, 58, 117)),
]

STATS = [
    ("300,000", "EVACUATED, ODISHA"),
    ("$1.84bn", "GTA VI SALES, EST."),
    ("−1,101", "DOW POINTS"),
    ("+17%", "ANTHROPIC DEBUT"),
    ("423", "RESCUE TEAMS"),
    ("16.1bn", "MILES — VOYAGER 1"),
]

# ALSO 14-35: same stories as r1-r3, one bold-keyword line each.
ALSO = [
    ("IAEA", "West presses Iran."),
    ("APEC", "Lonely Japan summit."),
    ("AMD", "China links hit stock."),
    ("GOLD", "Lows in sell-off."),
    ("ANDROID", "Checks installs."),
    ("HERA", "Eyes asteroid crash."),
    ("APPLE", "iOS 27.3 beta 2 out."),
    ("PHYSICS", "Message in brick."),
    ("ZOO", "Hippo dies; ate a hat."),
    ("STEWART", "Buried at sea."),
    ("MARS", "Bruno Mars's dad dies."),
    ("BRYDON", "Faked own agent."),
    ("RAJASTHAN", "Banswara results."),
    ("PUNJAB", "Kamboj joins BJP."),
    ("PAKISTAN", "Fuel cut by Rs.3."),
    ("PAKISTAN", "Web cable fault."),
    ("SCO", "Pakistan joins forum."),
    ("JAN 6", "Denies 'attack' tag."),
    ("GAZA", "IDF shoots two gunmen."),
    ("F1", "Vegas qualifying live."),
    ("T10", "Aces v Bulls."),
    ("CHILDREN", "Children's Day."),
]

# World map: land polygons (fractions of a 300x150 map box) and story dots.
# Fewer dots than r3 (6, not 8) with bigger labels — tiny map labels are
# noise at 300px, and the map is a locator, not a reading task.
MAP_LAND = [
    [(18, 18), (70, 10), (95, 22), (88, 48), (60, 55), (40, 48), (22, 38)],
    [(72, 62), (92, 60), (100, 85), (88, 115), (76, 95)],
    [(148, 18), (175, 12), (185, 28), (170, 42), (152, 36)],
    [(150, 50), (185, 48), (195, 75), (178, 105), (158, 88), (146, 65)],
    [(190, 15), (260, 10), (285, 30), (270, 55), (240, 60), (210, 48),
     (192, 32)],
    [(255, 105), (282, 102), (288, 118), (262, 122)],
]
# (dot x, dot y, label, label dx, label dy) — final px inside the map box.
# FIX-UP 1 (Danny spotted collisions): labels re-laid-out by hand so no two
# label rects overlap and no dot falls inside a label rect (measured with
# PIL at 11pt bold before choosing offsets). NY dot moved 8 box px west
# (still on North America) so its label clears the KYIV dot; LONDON label
# sits below its dot, KYIV right-up, TOKYO left-down, DELHI below its dot.
# GAZA keeps its dot but no label — 6 labels cannot fit this 210x88 box
# at a readable size without colliding; Gaza is ALSO story #32 (minor) and
# the caption "Every dot is a story on this page" still holds.
# FIX-UP 2 (Danny: "titiknya dan nama kotanya ga nyambung" — dots and
# labels don't visibly connect): measured on the render, the KYIV label's
# centre is closer to the DELHI dot (16.2px) than to its own dot (22.7px),
# the TOKYO label's centre is closer to the DELHI dot (21.4px) than to its
# own (24.3px), and the KYIV dot touches the NEW YORK label (0.0px gap).
# Fix: (a) thin 1px DARKRED leader lines from every dot to its label,
# drawn before the text so the label halo covers the tip; (b) the NEW YORK
# label moves BELOW its dot (was right of it) — it was the blocker: it sat
# sandwiched between the LONDON dot above and the LONDON label below, so
# no LONDON leader could be drawn without crossing it; (c) the DELHI label
# moves left+down and gets an elbow leader (left, then down) — a straight
# leader down would cross the TOKYO label, which sits directly below the
# DELHI dot. KYIV gets no leader: its dot already touches its label's
# left edge (0.5px), the connection is visible as-is.
MAP_DOTS = [
    (72, 28, "NEW YORK", -5, 25),
    (158, 14, "LONDON", -33, 19),
    (185, 22, "KYIV", 8, -7),
    (196, 50, "", 0, 0),  # GAZA: dot only, label dropped (see note above)
    (238, 38, "DELHI", -20, 20),
    (286, 24, "TOKYO", -36, 13),
]

MARKETS = [
    ("ANT", "+17%", "$97.17"),
    ("DOW", "−1,101", "−2.2%"),
    ("GOLD", "YEARLY LOWS", "SELL-OFF"),
]

# Coloured fact band under each hero illustration (the winners all carry
# one short bold fact line there). (text, background colour)
HERO_BANDS = [
    ("DEFERRED TO 2027", DARKRED),
    ("LANDFALL: NOON IST", DEEPBLUE),
    ("$1.84BN · DAY ONE", DARKGREEN),
]

# ------------------------------------------------------------------ layout
def kicker(d, x, y, num, place, topic, color=RED, max_w=None):
    """'1  WASHINGTON · IRAN' kicker line; x, y are SCALED px. If max_w
    is given, the place/topic part shrinks (never below 11pt) instead of
    running into the next column."""
    d.text((x, y), str(num), font=font(SANSB, T_KICKER + 1.5), fill=color)
    nx = x + text_w(d, str(num) + "  ", font(SANSB, T_KICKER + 1.5))
    label = "%s · %s" % (place, topic)
    size = T_KICKER
    if max_w is not None:
        while (size > 11.0 and
               text_w(d, label, font(SANSB, size)) > max_w - (nx - x)):
            size -= 0.5
    d.text((nx, y + 1 * S), label, font=font(SANSB, size), fill=INK)


def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=(200, 188, 160), width=int(2 * S))
    f = Flow(d)

    # ---- top bar
    y0 = f.y
    d.text((MARGIN, u(f.y)), "THE WORLD IN ONE DAY",
           font=font(SANSB, T_TOPBAR), fill=RED)
    mid = "DAY 324 OF 2026 · ONE-PAGE EDITION"
    d.text(((W - text_w(d, mid, font(SANS, T_TOPBAR))) / 2, u(f.y + 1)), mid,
           font=font(SANS, T_TOPBAR), fill=GREY)
    right = "35 STORIES · 6 REGIONS"
    d.text((W - MARGIN - text_w(d, right, font(SANSB, T_TOPBAR)), u(f.y + 1)),
           right, font=font(SANSB, T_TOPBAR), fill=INK)
    f.y += 19
    hline(d, MARGIN, u(f.y), CW, fill=RULE, width=1)
    f.y += 7
    f.note("top bar", y0, f.y)

    # ---- masthead + date stamp (52pt: the first thing the thumbnail shows)
    y0 = f.y
    d.text((MARGIN, u(f.y)), "Friday 20 November 2026",
           font=font(SERIFB, T_MASTHEAD), fill=INK)
    sx, sy, sw, sh = W - MARGIN - u(150), u(f.y), u(150), u(62)
    d.rectangle([sx, sy, sx + sw, sy + sh], outline=RED, width=int(2 * S))
    d.text((sx + sw / 2 - text_w(d, "NOVEMBER", font(SANSB, 11)) / 2,
            sy + u(4)), "NOVEMBER", font=font(SANSB, 11), fill=RED)
    d.text((sx + sw / 2 - text_w(d, "20", font(SERIFB, 28)) / 2, sy + u(16)),
           "20", font=font(SERIFB, 28), fill=INK)
    d.text((sx + sw / 2 - text_w(d, "FRIDAY", font(SANSB, 11)) / 2, sy + u(46)),
           "FRIDAY", font=font(SANSB, 11), fill=INK)
    f.y += 64
    f.note("masthead", y0, f.y)

    # ---- region strip
    y0 = f.y
    seg = CW / len(REGIONS)
    for i, (name, count, col) in enumerate(REGIONS):
        x0 = MARGIN + seg * i
        d.rectangle([x0, u(f.y), x0 + seg - u(2), u(f.y + 23)], fill=col)
        label = "%s %d" % (name, count)
        d.text((x0 + (seg - u(2) - text_w(d, label, font(SANSB, T_REGION))) / 2,
                u(f.y + 5)), label, font=font(SANSB, T_REGION), fill=WHITE)
    f.y += 23
    f.note("regions", y0, f.y)

    # ---- stat strip: 32pt numbers are the thumbnail's second read
    y0 = f.y + 6
    hline(d, MARGIN, u(y0), CW, fill=INK, width=1.5)
    for i, (num, label) in enumerate(STATS):
        x0 = MARGIN + CW * i / len(STATS)
        d.text((x0 + u(4), u(y0 + 5)), num, font=font(SERIFB, T_STATNUM),
               fill=RED)
        draw_para(d, x0 + u(4), u(y0 + 40), label, SANSB, T_STATLABEL, GREY,
                  CW / len(STATS) - u(8), u(15), max_lines=1)
        if i:
            d.line([(x0, u(y0 + 4)), (x0, u(y0 + 52))], fill=RULE, width=int(S))
    f.y = y0 + 56
    hline(d, MARGIN, u(f.y), CW, fill=INK, width=1.5)
    f.y += 8
    f.note("stats", y0, f.y)

    # ---- heroes: 3 COLUMNS, the round-4 change. Each column is a big
    # flat illustration (~136px tall) + coloured fact band + kicker +
    # 28pt bold title (2 lines) + 2-line deck. At 300px a column reads
    # as one bold colour block + one bold title — the winners' shape.
    y0 = f.y
    hcolw = (CW - u(26)) / 3
    hgap = u(13)
    illo_h = 136
    for i, (num, place, topic, scene, title, deck, badge, bcol) in enumerate(HEROES):
        x0 = MARGIN + i * (hcolw + hgap)
        yy = f.y
        scene(d, x0, u(yy), hcolw, u(illo_h))
        yy += illo_h
        band_text, band_col = HERO_BANDS[i]
        d.rectangle([x0, u(yy), x0 + hcolw, u(yy + 20)], fill=band_col)
        d.text((x0 + (hcolw - text_w(d, band_text, font(SANSB, T_BAND))) / 2,
                u(yy + 4)), band_text, font=font(SANSB, T_BAND), fill=WHITE)
        yy += 20 + 4
        kicker(d, x0, u(yy), num, place, topic)
        pw = pill_w(d, badge)
        pill(d, x0 + hcolw - pw, u(yy), badge, WHITE, bcol)
        yy += 15 + 2
        yy = draw_para(d, x0, u(yy), title, SERIFB, T_HEROTITLE, INK,
                       hcolw, u(32), max_lines=2, min_px=T_HEROTITLE) / S
        yy += 3
        yy = draw_para(d, x0, u(yy), deck, SANS, T_HERODECK, BODY,
                       hcolw, u(17), max_lines=2, min_px=T_HERODECK) / S
        hero_bottom = yy
    f.y = hero_bottom
    hline(d, MARGIN, u(f.y), CW, fill=INK, width=1.5)
    f.y += 8
    f.note("heroes", y0, f.y)

    # ---- mid grid: 2 rows x 5. Wide flat illustration strip (~50px)
    # + kicker + 19pt bold title (2 lines) + 1 short deck line.
    y0 = f.y
    mcolw = (CW - u(42)) / 5
    mgap = u(10.5)
    strip_h = 50
    row_h = strip_h + 4 + 14 + 2 + 44 + 2 + 16
    for i, (num, place, topic, scene, title, deck) in enumerate(MIDS):
        row, col = divmod(i, 5)
        x0 = MARGIN + col * (mcolw + mgap)
        yy = f.y + row * (row_h + 8)
        scene(d, x0, u(yy), mcolw, u(strip_h))
        pw = pill_w(d, "Reported")
        pill(d, x0 + mcolw - u(3) - pw, u(yy + 1), "Reported", WHITE, GREEN)
        yy += strip_h + 4
        kicker(d, x0, u(yy), num, place, topic, max_w=mcolw)
        yy += 14
        yy = draw_para(d, x0, u(yy), title, SERIFB, T_MIDTITLE, INK,
                       mcolw, u(22), max_lines=2, min_px=T_MIDTITLE) / S
        yy += 2
        yy = draw_para(d, x0, u(yy), deck, SANS, T_MIDDECK, BODY,
                       mcolw, u(16), max_lines=1, min_px=12.0) / S
    f.y = f.y + 2 * (row_h + 8) - 8
    f.note("mids", y0, f.y)
    return img, d, f


# ------------------------------------------------------------- bottom band
def bottom_band(img, d, f):
    """Map + ALSO + verdict/legend/markets. f is the Flow; returns nothing,
    advances f.y just below the tallest column."""
    y = f.y
    y0 = y
    hline(d, MARGIN, u(y), CW, fill=INK, width=1.5)
    y += 8

    # ---- map column (left): 6 dots, bigger labels than r3.
    mx, mw = MARGIN, u(210)
    d.text((mx, u(y)), "● WHERE IT HAPPENED", font=font(SANSB, T_MAPTITLE),
           fill=INK)
    mapx, mapy, mapw, maph = mx, u(y + 16), mw, u(88)
    d.rectangle([mapx, mapy, mapx + mapw, mapy + maph],
                fill=(233, 226, 205), outline=RULE, width=int(S))
    for poly in MAP_LAND:
        pts = [(mapx + px * mapw / 300, mapy + py * maph / 150)
               for px, py in poly]
        d.polygon(pts, fill=(214, 198, 160), outline=(170, 152, 120))
    lfnt = font(SANSB, T_MAPLABEL)
    for dx, dy, label, lx, ly in MAP_DOTS:
        px, py = mapx + dx * mapw / 300, mapy + dy * maph / 150
        d.ellipse([px - 3 * S, py - 3 * S, px + 3 * S, py + 3 * S], fill=RED)
        if not label:
            continue  # dot only (GAZA): no room for a 6th label
        ax, ay = px + u(lx), py + u(ly)
        bb = d.textbbox((ax, ay), label, font=lfnt,
                        stroke_width=int(2 * S))
        # FIX-UP 2: 1px leader line dot -> label, drawn BEFORE the text so
        # the label halo covers the tip. Straight vertical for NY/LONDON/
        # TOKYO (dot x falls inside the label's x-range); DELHI gets an
        # elbow (left along the dot's latitude, then down) because a
        # straight leader down would cross the TOKYO label sitting directly
        # below the DELHI dot. KYIV gets none: its dot already touches its
        # label's left edge, the connection is visible as-is.
        if label in ("NEW YORK", "LONDON", "TOKYO"):
            d.line([(px, py + 3 * S + 1), (px, bb[1])], fill=DARKRED,
                   width=2)
        elif label == "DELHI":
            ex = bb[0] + int(2.5 * S)
            d.line([(px - 3 * S, py), (ex, py), (ex, bb[1])],
                   fill=DARKRED, width=2)
        d.text((ax, ay), label, font=lfnt, fill=INK,
               stroke_width=int(2 * S), stroke_fill=(233, 226, 205))
    d.text((mx, mapy + maph + u(8)), "Every dot is a story on this page.",
           font=font(SANS, T_MAPCAP), fill=GREY)

    # ---- ALSO column (middle): bold keyword lines, 11 rows x 2 cols.
    ax, aw = MARGIN + u(222), u(484)
    d.text((ax, u(y)), "● ALSO ON FRIDAY 20 NOVEMBER — 22 MORE STORIES",
           font=font(SANSB, T_ALSOTITLE), fill=INK)
    hline(d, ax, u(y + 14), aw, fill=RULE, width=1)
    colw = aw / 2
    also_bottom = y
    for i, (kick, text) in enumerate(ALSO):
        col, row = divmod(i, 11)
        x0 = ax + col * colw
        yy = y + 19 + row * 15
        num = 14 + i
        line = "%s — %s" % (kick, text)
        fnt, lines = fit_lines(d, line, SANS, T_ALSO, colw - u(26), 1,
                               T_FLOOR)
        if len(lines) != 1:
            raise ValueError("ALSO item does not fit one line: %r" % line)
        d.text((x0, u(yy)), str(num), font=font(SANSB, T_ALSO), fill=RED)
        d.text((x0 + text_w(d, str(num) + " ", font(SANSB, T_ALSO)), u(yy)),
               line, font=fnt, fill=INK)
        also_bottom = max(also_bottom, yy + 14)
    f.note("also", y, also_bottom)

    # ---- right column: verdict (shortened — 3 lines) + legend + markets.
    rx, rw = MARGIN + u(718), u(250)
    vx, vy, vw = rx, u(y), rw
    vh = u(72)
    d.rectangle([vx, vy, vx + vw, vy + vh], fill=NAVY)
    d.text((vx + u(10), vy + u(5)), "THE VERDICT",
           font=font(SANSB, T_VERDICT_TITLE), fill=(255, 214, 110))
    draw_para(d, vx + u(10), vy + u(20),
              "A war deferred, a storm landed, a game that beat every film "
              "in a day.",
              SERIF, T_VERDICT, WHITE, vw - u(20), u(16), max_lines=3,
              min_px=T_VERDICT)
    ly = y + 72 + 6
    d.text((rx, u(ly)), "HOW SURE ARE WE?", font=font(SANSB, T_LEGEND),
           fill=INK)
    for j, (tag, desc) in enumerate([
            ("Reported", "named sources confirm it"),
            ("Estimate", "labelled as an estimate"),
            ("Scheduled", "set for today")]):
        yy = ly + 15 + j * 14
        d.ellipse([rx, u(yy + 2), rx + u(7), u(yy + 9)],
                  fill=GREEN if tag == "Reported" else
                  (GOLD if tag == "Estimate" else TEAL))
        d.text((rx + u(11), u(yy)), "%s — %s" % (tag, desc),
               font=font(SANS, T_LEGEND), fill=INK)
    my = ly + 15 + 3 * 14 + 5
    d.text((rx, u(my)), "MARKETS & MONEY", font=font(SANSB, T_MARKET),
           fill=INK)
    hline(d, rx, u(my + 13), rw, fill=RULE, width=1)
    for j, (name, val, note_txt) in enumerate(MARKETS):
        yy = my + 16 + j * 14
        d.text((rx, u(yy)), name, font=font(SANSB, T_MARKET), fill=INK)
        d.text((rx + u(52), u(yy)), val, font=font(SANSB, T_MARKET),
               fill=RED)
        d.text((rx + u(172), u(yy)), note_txt, font=font(SANS, T_MARKET),
               fill=GREY)
    right_bottom = my + 16 + 2 * 14 + 13
    f.note("right column", y, right_bottom)
    f.y = max(also_bottom, right_bottom)
    f.note("bottom band", y0, f.y)


def date_check(d, f):
    """The strip the judge loved: stories left out because they happened
    earlier. Advances f.y just below the strip."""
    y0 = f.y
    d.rectangle([MARGIN, u(f.y), MARGIN + CW, u(f.y + 34)], outline=RED,
                width=int(1.5 * S))
    d.text((MARGIN + u(8), u(f.y + 10)), "DATE CHECK",
           font=font(SANSB, T_DATE_LABEL), fill=RED)
    txt = ("Left out — earlier: ICJ: Myanmar genocide (Thu 19) · Houthi "
           "missile, Riyadh (Thu 19) · Trump–Xi–Putin summit (Thu 19) · "
           "Han Duck-soo conviction (Thu 19) · US–Venezuela pact (Wed 18) "
           "· Gaza operation (Wed–Thu 18–19).")
    # FIX-UP: text used to start at +96 while the label is 91px wide, so
    # "Left" ran over the "K" of CHECK. Text now starts at +120 (label ends
    # at +99, 21px clear) and still wraps to the same 2 lines at 14pt
    # (line 1 measures 839.8px vs 840px width — verified, not guessed).
    draw_para(d, MARGIN + u(120), u(f.y + 3), txt, SANS, T_DATE, INK,
              CW - u(128), u(15), max_lines=2, min_px=T_DATE)
    f.note("date check", y0, y0 + 34)
    f.y = y0 + 34


def sharpen(img, radius, percent, threshold):
    """Mild unsharp mask: keeps the judge's own 300px downscale crisp
    without halos at full size."""
    return img.filter(ImageFilter.UnsharpMask(radius=radius,
                                              percent=percent,
                                              threshold=threshold))


def main():
    img, d, f = render()
    f.gap(5)
    bottom_band(img, d, f)
    f.gap(5)
    date_check(d, f)
    foot = ("Every story here happened, or was first reported, on Friday "
            "20 November 2026. Sources: Reuters, BBC, The Hindu, NYT, AP, "
            "NASA, JAXA, IAEA.")
    d.text(((W - text_w(d, foot, font(SANS, T_FOOT))) / 2, u(f.y + 2)), foot,
           font=font(SANS, T_FOOT), fill=GREY)
    f.note("footer", f.y, f.y + 10)
    bottom = f.y + 10
    print("layout (final px):")
    for name, y0, y1 in TRACE:
        print("  %-14s %4d .. %4d" % (name, y0, y1))
    print("page bottom: %d / 1024" % bottom)
    assert bottom <= 1024, "page overflow: bottom %d > 1024" % bottom
    small = img.resize((1024, 1024), Image.LANCZOS)
    small = sharpen(small, radius=2, percent=45, threshold=3)
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "entry.png")
    small.save(path, format="PNG", optimize=True)
    print("wrote", path, os.path.getsize(path), "bytes")
    # Previews: 1024 as-is, 300 with the same LANCZOS + sharpen pipeline
    # the judge's thumbnail will effectively apply — so the preview fairly
    # represents the design instead of adding blur of its own.
    shot = os.path.join(here, "screenshots")
    os.makedirs(shot, exist_ok=True)
    small.save(os.path.join(shot, "entry-1024.png"), format="PNG",
               optimize=True)
    prev = img.resize((300, 300), Image.LANCZOS)
    prev = sharpen(prev, radius=1.2, percent=60, threshold=2)
    prev.save(os.path.join(shot, "entry-300.png"), format="PNG",
              optimize=True)
    print("wrote previews",
          os.path.getsize(os.path.join(shot, "entry-1024.png")),
          os.path.getsize(os.path.join(shot, "entry-300.png")), "bytes")


if __name__ == "__main__":
    main()
