#!/usr/bin/env python3
"""Generate every SVG illustration (cover + per-chapter figures) deterministically. Stdlib only."""
from __future__ import annotations
from html import escape
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'illustrations'
BG, INK, MUTED, LINE = '#f7f5ef', '#232a33', '#5d6873', '#d8d4c8'
INDIGO, TERRA, TEAL, SOFT = '#5a4fcf', '#d0693a', '#2f8f83', '#ece9e0'
FONT = 'system-ui, -apple-system, "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", Meiryo, sans-serif'


class Figure:
    def __init__(self, number: int, title: str, subtitle: str, height: int = 680, part: str = '', code: str = 'RELEVANCE', accent: str = INDIGO, subdir: str = '', header: bool = True):
        self.h = height
        self.n = number
        self.part = part
        self.code = code
        self.accent = accent
        self.subdir = subdir
        self.defs: list[str] = ['<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="#5d6873" stroke-width="1.4"/></marker>']
        self.body: list[str] = []
        self.title = title
        self.subtitle = subtitle
        self.gradients = 0
        if not header:
            return  # 扉絵：見出しも文字も描かない（title/desc は aria 用にのみ残る）
        shown = str(ord(part) - 96) if part.isalpha() and len(part) == 1 else part  # a→1, b→2 … or an explicit number
        label = code if number == 0 else f'{code}     {number:02d}' + (f'     図{number}-{shown}' if part else '')
        self.text(50, 52, label, 18, accent, weight=700)
        self.text(50, 103, title, 34, weight=700)
        self.text(50, 141, subtitle, 21, MUTED)
        self.line(50, 166, 1150, 166, color=LINE, width=1)

    def text(self, x, y, s, size=24, color=INK, anchor='start', weight=400):
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>')

    def line(self, x1, y1, x2, y2, color=MUTED, width=2, arrow=False, dash=False):
        extra = (' marker-end="url(#arrow)"' if arrow else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def path(self, d, color=MUTED, width=2, arrow=False, dash=False, fill='none'):
        extra = (' marker-end="url(#arrow)"' if arrow else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.body.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def box(self, x, y, w, h, title, subtitle='', color=INDIGO, size=24, dash=False):
        extra = ' stroke-dasharray="8 7"' if dash else ''
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="{color}" stroke-width="2"{extra}/>')
        self.text(x + w / 2, y + (h / 2 + 8 if not subtitle else h / 2 - 4), title, size, color, anchor='middle', weight=700)
        if subtitle:
            self.text(x + w / 2, y + h / 2 + 28, subtitle, 19, MUTED, anchor='middle')

    def circ(self, x, y, r=10, color=INDIGO, fill=True, dash=False, width=2):
        if fill:
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>')
        else:
            extra = ' stroke-dasharray="7 6"' if dash else ''
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="{color}" stroke-width="{width}"{extra}/>')

    def panel(self, x, y, w, h, label=''):
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#c9c4b6" stroke-width="2" stroke-dasharray="7 7"/>')
        if label:
            self.text(x + w / 2, y + 34, label, 23, INK, anchor='middle', weight=700)

    def blob(self, cx, cy, r, color, opacity=0.55):
        """A soft-edged disc: the visual sign of a distribution without a boundary."""
        self.gradients += 1
        gid = f'g{self.code[:3].lower()}{self.n:02d}{self.part}-{self.gradients}'
        self.defs.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{opacity}"/><stop offset="0.55" stop-color="{color}" stop-opacity="{opacity*0.45:.2f}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')
        self.body.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="url(#{gid})"/>')

    def gauss(self, cx, base, height, sigma, x0, x1, color=INDIGO, width=3, fill=''):
        pts = []
        steps = 90
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i / steps
            y = base - height * math.exp(-((x - cx) ** 2) / (2 * sigma ** 2))
            pts.append(f'{x:.1f},{y:.1f}')
        if fill:
            self.body.append(f'<polygon points="{x0:.1f},{base:.1f} {" ".join(pts)} {x1:.1f},{base:.1f}" fill="{fill}" opacity="0.35"/>')
        self.body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    @staticmethod
    def gy(x, cx, base, height, sigma):
        return base - height * math.exp(-((x - cx) ** 2) / (2 * sigma ** 2))

    def person(self, x, y, angle, color=INDIGO, r=9):
        """A head with a short arrow showing the direction the person faces."""
        self.circ(x, y, r, color)
        self.line(x, y, x + 26 * math.cos(angle), y + 26 * math.sin(angle), color=color, width=2.5, arrow=True)

    def footer(self, s):
        if s:
            self.text(50, self.h - 28, s, 19, MUTED)

    def save(self, name: str):
        out = OUT / self.subdir if self.subdir else OUT
        out.mkdir(parents=True, exist_ok=True)
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.h}" viewBox="0 0 1200 {self.h}" role="img" aria-labelledby="title desc">',
                f'<title id="title">{escape(self.title)}</title>', f'<desc id="desc">{escape(self.subtitle)}</desc>',
                '<defs>' + ''.join(self.defs) + '</defs>', f'<rect width="1200" height="{self.h}" rx="20" fill="{BG}"/>',
                f'<g font-family=\'{FONT}\'>']
        (out / name).write_text('\n'.join(head + self.body + ['</g>', '</svg>']) + '\n', encoding='utf-8')
        return (self.subdir + '/' + name) if self.subdir else name


def spread(cx, cy, r, n, seed):
    """Deterministic quasi-uniform points in a disc (golden-angle spiral)."""
    pts = []
    for i in range(n):
        t = (i + seed) * 2.399963
        rr = r * math.sqrt((i + 0.5) / n)
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts


def radial_tree(f, tx, ty, radii, branches, color_by_depth, leaf_r=(4, 3, 2.5), spread_deg=(0.4, 0.18, 0.08)):
    """Draw a three-level tree radiating from (tx, ty) with the given ring radii."""
    for r in radii:
        f.circ(tx, ty, r, LINE, fill=False)
    f.circ(tx, ty, 6, INDIGO)
    for k in range(branches):
        a1 = -math.pi / 2 + k * 2 * math.pi / branches
        p1 = (tx + radii[0] * math.cos(a1), ty + radii[0] * math.sin(a1))
        f.line(tx, ty, *p1, color=color_by_depth[0], width=1.5)
        f.circ(*p1, leaf_r[0], color_by_depth[0])
        for j in (-spread_deg[1], spread_deg[1]):
            p2 = (tx + radii[1] * math.cos(a1 + j), ty + radii[1] * math.sin(a1 + j))
            f.line(*p1, *p2, color=color_by_depth[1], width=1.2)
            f.circ(*p2, leaf_r[1], color_by_depth[1])
            for m in (-spread_deg[2], spread_deg[2]):
                p3 = (tx + radii[2] * math.cos(a1 + j + m), ty + radii[2] * math.sin(a1 + j + m))
                f.line(*p2, *p3, color=color_by_depth[2], width=1)
                f.circ(*p3, leaf_r[2], color_by_depth[2])


def pipeline(f, y, label_gen, label_mid, gate_title, gate_sub, out_a, out_b, color=TERRA):
    """A generation -> candidate -> gate -> two outcomes row, used twice in 10-c."""
    f.box(70, y, 230, 80, label_gen, '', INDIGO, 22)
    f.line(305, y + 40, 360, y + 40, color=MUTED, width=2, arrow=True)
    f.body.append(f'<rect x="365" y="{y}" width="230" height="80" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>')
    f.text(480, y + 47, label_mid, 20, INK, anchor='middle')
    f.line(600, y + 40, 655, y + 40, color=MUTED, width=2, arrow=True)
    f.box(660, y - 8, 260, 96, gate_title, gate_sub, color, 22)
    f.line(925, y + 40, 975, y + 40, color=MUTED, width=2, arrow=True)
    f.text(1060, y + 30, out_a, 19, TEAL, anchor='middle', weight=700)
    f.text(1060, y + 60, out_b, 19, TERRA, anchor='middle', weight=700)


SERIES_FILES = ['series.json', 'series-2/series.json']


def main() -> None:
    series = json.loads((ROOT / 'series.json').read_text(encoding='utf-8'))
    expected = {'00-cover.svg'}
    for sf in SERIES_FILES:
        s = json.loads((ROOT / sf).read_text(encoding='utf-8'))
        expected |= {str(Path(p).relative_to('assets/illustrations')) for c in s['chapters'] for p in c['figures']}
        expected |= {str(Path(p['opener']).relative_to('assets/illustrations')) for p in s.get('parts', []) if p.get('opener')}
    made: set[str] = set()

    # 00 cover
    f = Figure(0, 'RELEVANCE ── 意味の関連性に関する考察', 'LLMを逆再生して「意味」を知る、全12回', 660)
    f.blob(400, 390, 175, INDIGO)
    f.blob(640, 390, 175, TEAL)
    f.text(345, 395, '意味 A', 26, INDIGO, anchor='middle', weight=700)
    f.text(700, 395, '意味 B', 26, TEAL, anchor='middle', weight=700)
    f.text(520, 395, '関係', 24, INK, anchor='middle', weight=700)
    f.text(520, 425, 'それ自体が分布', 17, MUTED, anchor='middle')
    f.circ(520, 232, 12, TERRA)
    f.text(520, 215, '媒介', 19, TERRA, anchor='middle', weight=700)
    f.path('M 400 330 C 430 265 480 240 508 236', color=TERRA, width=2, dash=True)
    f.path('M 640 330 C 610 265 560 240 532 236', color=TERRA, width=2, dash=True)
    f.text(960, 340, '意味は、点でも集合でもなく分布。', 23, INK, anchor='middle')
    f.text(960, 380, '関係もまた分布。', 23, INK, anchor='middle')
    f.text(960, 420, '関連は見出され、言葉に固定され、', 23, INK, anchor='middle')
    f.text(960, 460, '検証されて、世界の側に置かれる。', 23, INK, anchor='middle')
    f.text(600, 585, '関連は仮説であり、評価がそれを検証する。', 30, INDIGO, anchor='middle', weight=700)
    f.footer('AIを研究するのではなく、AIという媒体を通して人間について考える。')
    made.add(f.save('00-cover.svg'))

    # 01-a reverse playback
    f = Figure(1, '仕組みを知るのではなく、振る舞いを逆再生する', 'LLMの「分かっているように見える」を手がかりに、意味とは何かへ戻る', 560, 'a')
    f.box(80, 250, 330, 150, 'LLM', '確率的に尤もらしい次の語を選ぶ', INDIGO, 30)
    for i, (w, p) in enumerate([('鳥が', 0.9), ('飛ぶ', 0.72), ('泳ぐ', 0.18), ('鳴く', 0.44)]):
        y = 260 + i * 34
        f.text(455, y + 22, w, 19, INK)
        f.body.append(f'<rect x="520" y="{y+6}" width="{int(140*p)}" height="18" rx="4" fill="{INDIGO}" opacity="{0.35+0.5*p:.2f}"/>')
    f.text(590, 415, '次の語の確率', 17, MUTED, anchor='middle')
    f.box(790, 250, 330, 150, '意味とはなにか', '人間の側で起きていること', TEAL, 30)
    f.line(700, 325, 785, 325, color=TEAL, width=3, arrow=True)
    f.text(742, 305, '見えるもの', 16, MUTED, anchor='middle')
    f.line(785, 365, 700, 365, color=TERRA, width=3, arrow=True)
    f.text(742, 392, '逆再生', 18, TERRA, anchor='middle', weight=700)
    f.text(600, 480, '知性があるように見える、という事実のほうから、意味の正体へ戻る', 19, INK, anchor='middle')
    f.footer('')
    made.add(f.save('01-a-reverse-playback.svg'))

    # 01-b steam engine
    f = Figure(1, '先に動いていたものから、原理が読み取られる', '理論より先に機関が動いていた。LLMについても同じ順序で考える', 460, 'b')
    f.box(130, 230, 300, 90, '蒸気機関', '先に動いていた', MUTED, 24)
    f.line(435, 275, 545, 275, arrow=True)
    f.text(490, 262, '後から', 16, MUTED, anchor='middle')
    f.box(550, 230, 300, 90, '熱力学', '原理が追いついた', MUTED, 24)
    f.box(130, 345, 300, 70, 'LLM', '人間らしく振る舞う', INDIGO, 22)
    f.line(435, 380, 545, 380, arrow=True, dash=True)
    f.text(490, 368, 'これから', 16, MUTED, anchor='middle')
    f.box(550, 345, 300, 70, '意味・知性の説明', 'まだ追いついていない', TEAL, 22)
    f.text(1000, 300, '先行するモデルが', 21, INK, anchor='middle', weight=700)
    f.text(1000, 330, '本質を暗示する', 21, INK, anchor='middle', weight=700)
    f.footer('')
    made.add(f.save('01-b-steam-engine.svg'))

    # 02-a line and premises
    f = Figure(2, '「似ている」は、二点を結ぶ一本の線ではない', '線は見る側の前提の中にあり、前提が違えば判定は割れる', 620, 'a')
    f.panel(100, 205, 440, 360, '頭の中のイメージ')
    f.circ(190, 380, 13, INDIGO); f.circ(450, 380, 13, TEAL)
    f.line(203, 380, 437, 380, color=INK, width=3)
    f.text(190, 425, 'A', 22, INDIGO, anchor='middle', weight=700); f.text(450, 425, 'B', 22, TEAL, anchor='middle', weight=700)
    f.text(320, 360, '線がある？', 19, MUTED, anchor='middle')
    f.text(320, 500, '線は、AとBの間にはなく', 18, INK, anchor='middle')
    f.text(320, 526, '見る側の前提の中にある', 18, INK, anchor='middle')
    f.panel(640, 205, 460, 360, '不揃いな前提')
    f.text(870, 265, 'トマト と リンゴ', 21, INK, anchor='middle', weight=700)
    f.box(700, 295, 340, 62, '台所：違う', '野菜と果物', TERRA, 20)
    f.box(700, 375, 340, 62, '植物学：同じ', 'どちらも果実', TEAL, 20)
    f.box(700, 455, 340, 62, '食卓：似ている', '赤くて丸い', INDIGO, 20)
    f.text(870, 548, 'どれも正しい。前提が違うだけ', 17, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('02-a-line-and-premises.svg'))

    # 02-b blue green
    f = Figure(2, '境界は明確か？', '青から緑へ連続した帯のどこにも、境目は引けない', 460, 'b')
    f.defs.append('<linearGradient id="g02b-bar" x1="0" x2="1"><stop offset="0" stop-color="#2b5fd9"/><stop offset="1" stop-color="#2fa36a"/></linearGradient>')
    f.body.append('<rect x="150" y="235" width="900" height="70" rx="12" fill="url(#g02b-bar)"/>')
    f.text(150, 340, '青', 24, '#2b5fd9', weight=700); f.text(1050, 340, '緑', 24, '#2fa36a', anchor='end', weight=700)
    for x in (330, 510, 690, 870):
        f.line(x, 235, x, 305, color='#ffffff', width=1.5, dash=True)
        f.text(x, 225, '？', 18, MUTED, anchor='middle')
    f.text(600, 345, 'どこから緑？', 22, INK, anchor='middle', weight=700)
    f.text(600, 395, '言葉には輪郭があるが、言葉が指すものには輪郭がない', 19, INK, anchor='middle')
    f.footer('')
    made.add(f.save('02-b-blue-green.svg'))

    # 03-a three models (new)
    f = Figure(3, '意味の形：点か、集合か、分布か', '同じ「鳥」を三つのモデルで描く', 640, 'a')
    f.panel(60, 205, 340, 390, '点：一つの定義')
    f.circ(230, 390, 11, INDIGO)
    f.line(230, 379, 230, 330, color=INDIGO, width=2); f.text(230, 318, '「鳥」', 22, INDIGO, anchor='middle', weight=700)
    f.text(230, 440, '動かない。当てはまるか', 16, MUTED, anchor='middle'); f.text(230, 462, '当てはまらないかだけ', 16, MUTED, anchor='middle')
    f.text(230, 560, '意味の揺れを説明できない', 16, INK, anchor='middle')
    f.panel(430, 205, 340, 390, '集合：中か外か')
    f.body.append(f'<rect x="490" y="275" width="220" height="200" rx="18" fill="#ffffff" stroke="{INDIGO}" stroke-width="3"/>')
    for name, x, y in [('スズメ', 560, 330), ('カラス', 650, 330), ('ペンギン', 600, 420)]:
        f.circ(x, y - 18, 6, INDIGO); f.text(x, y + 6, name, 16, INK, anchor='middle')
    f.circ(600, 525, 6, MUTED); f.text(600, 548, 'コウモリ', 16, MUTED, anchor='middle')
    f.text(600, 580, 'スズメとペンギンの違いを説明できない', 15, INK, anchor='middle')
    f.panel(800, 205, 340, 390, '分布：濃淡')
    f.blob(970, 390, 140, INDIGO, 0.6)
    f.circ(970, 390, 6, INDIGO); f.text(970, 372, 'スズメ', 16, INK, anchor='middle', weight=700)
    f.circ(1010, 420, 5, INDIGO); f.text(1030, 440, 'カラス', 15, INK, anchor='middle')
    f.circ(885, 470, 5, TERRA); f.text(885, 492, 'ペンギン', 15, TERRA, anchor='middle')
    f.circ(1095, 540, 4, MUTED); f.text(1095, 562, 'コウモリ', 14, MUTED, anchor='middle')
    f.text(970, 580, '高さの違いとして表せる', 15, INK, anchor='middle')
    f.footer('')
    made.add(f.save('03-a-three-models.svg'))

    # 03-b bird mountain
    f = Figure(3, '意味は、ぼやけた縁を持つぼやけた丸', '砂の山：頂上が典型例、裾はどこまでも薄く続き、ゼロにならない', 660, 'b')
    cx, base, h, s = 560, 520, 290, 125
    f.gauss(cx, base, h, s, 70, 1130, INDIGO, 3, fill='#c9c4ee')
    f.line(70, base, 1130, base, color=LINE, width=2)
    for name, x in [('スズメ', 560), ('ハト', 505), ('カラス', 620), ('カモ', 690), ('ニワトリ', 770), ('ダチョウ', 850), ('ペンギン', 925), ('コウモリ', 1035)]:
        y = f.gy(x, cx, base, h, s)
        f.circ(x, y, 7, TERRA if name != 'スズメ' else INDIGO)
        f.line(x, y + 9, x, base - 4, color=LINE, width=1, dash=True)
        f.text(x, base + 30, name, 17, INK, anchor='middle')
    f.text(560, 205, '高さ ＝ どれだけ典型的か', 22, INDIGO, anchor='middle', weight=700)
    f.text(1035, base + 56, '外ではなく、', 15, MUTED, anchor='middle'); f.text(1035, base + 76, 'ほとんど高さがないだけ', 15, MUTED, anchor='middle')
    f.line(200, 480, 120, 512, color=TERRA, width=2, arrow=True)
    f.text(215, 470, '縁はない：薄くなるが消えない', 17, TERRA)
    f.text(180, base + 30, '「鳥」の山', 19, MUTED, anchor='middle', weight=700)
    f.footer('白か黒かは決められないが、どれくらい灰色かは決められる。')
    made.add(f.save('03-b-bird-mountain.svg'))

    # 03-c sharp and flat
    f = Figure(3, '散らばりの大きさが、山の形を決める', '尖った山は少し外れると当てはまらず、平たい山はほとんど何でも当てはまる', 480, 'c')
    f.gauss(330, 420, 190, 32, 160, 500, TEAL, 3, fill='#bfe3dd'); f.line(160, 420, 500, 420, color=LINE, width=2)
    f.text(330, 215, '尖った山：正三角形', 21, TEAL, anchor='middle', weight=700)
    f.text(330, 450, '典型から少し外れただけで当てはまらない', 15, MUTED, anchor='middle')
    f.gauss(870, 420, 80, 120, 640, 1100, TERRA, 3, fill='#f2d2c2'); f.line(640, 420, 1100, 420, color=LINE, width=2)
    f.text(870, 215, '平たい山：道具・もの', 21, TERRA, anchor='middle', weight=700)
    f.text(870, 450, '裾が遠くまで広がり、ほとんど何でも当てはまる', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('03-c-sharp-and-flat.svg'))

    # 04-a crowd (new)
    f = Figure(4, '全員が同じ方向を向いた群衆', '「同じ方向を見ている二人」という観察は、周りがばらばらなときにだけ意味を持つ', 620, 'a')
    f.panel(60, 205, 520, 380, 'ばらばらの向き')
    for i, (x, y) in enumerate(spread(320, 400, 135, 22, 2)):
        ang = (i * 2.399963) % (2 * math.pi)
        f.person(x, y, ang, INDIGO)
    (ax, ay), (bx, by) = spread(320, 400, 135, 22, 2)[3], spread(320, 400, 135, 22, 2)[15]
    f.person(ax, ay, -0.9, TERRA); f.person(bx, by, -0.9, TERRA)
    f.text(320, 570, '同じ方向を見ている二人：何か共通の関心があるかもしれない', 15, INK, anchor='middle')
    f.panel(620, 205, 520, 380, '全員が同じ向き')
    for i, (x, y) in enumerate(spread(880, 400, 135, 22, 2)):
        f.person(x, y, -0.9, TERRA if i in (3, 15) else INDIGO)
    f.text(880, 570, '同じ方向を見ている二人：何も教えてくれない。全員がそうだから', 15, INK, anchor='middle')
    f.footer('')
    made.add(f.save('04-a-crowd.svg'))

    # 04-b isotropy vs anisotropy
    f = Figure(4, '空間そのものが、ある方向に歪んで圧縮されている', '等方的な散らばり（素朴な絵）と、狭い円錐に密集する異方性（実測）', 680, 'b')
    f.panel(60, 205, 480, 400, '等方的：どの方向にも同じ')
    f.circ(300, 420, 150, LINE, fill=False)
    for x, y in spread(300, 420, 140, 70, 1):
        f.circ(x, y, 5, INDIGO)
    a, b = (300 + 140 * math.cos(2.2), 420 + 140 * math.sin(2.2)), (300 + 140 * math.cos(-0.5), 420 + 140 * math.sin(-0.5))
    f.circ(*a, 8, TERRA); f.circ(*b, 8, TERRA)
    f.line(300, 420, *a, color=TERRA, width=2); f.line(300, 420, *b, color=TERRA, width=2)
    f.text(300, 590, '無関係なものは、遠く見える', 18, INK, anchor='middle')
    f.panel(620, 205, 520, 400, '異方的：全員が同じ方向を向く')
    ox, oy = 680, 560
    f.line(ox, oy, 1110, 290, color=LINE, width=2); f.line(ox, oy, 1110, 410, color=LINE, width=2)
    for i in range(70):
        t = (i * 0.618034) % 1.0
        d = 70 + 350 * math.sqrt(((i * 7) % 70) / 70)
        ang = math.atan2(290 - oy, 1110 - ox) * (1 - t) + math.atan2(410 - oy, 1110 - ox) * t
        f.circ(ox + d * math.cos(ang), oy + d * math.sin(ang), 5, INDIGO)
    pa = (ox + 300 * math.cos(math.atan2(290 - oy, 1110 - ox)), oy + 300 * math.sin(math.atan2(290 - oy, 1110 - ox)))
    pb = (ox + 330 * math.cos(math.atan2(410 - oy, 1110 - ox)), oy + 330 * math.sin(math.atan2(410 - oy, 1110 - ox)))
    f.circ(*pa, 8, TERRA); f.circ(*pb, 8, TERRA)
    f.line(ox, oy, *pa, color=TERRA, width=2); f.line(ox, oy, *pb, color=TERRA, width=2)
    f.text(1010, 262, '角度が小さい', 17, TERRA, weight=700); f.text(1010, 284, '＝ 似て見える', 17, TERRA, weight=700)
    f.text(880, 590, '無関係なものまで、近く見える', 18, INK, anchor='middle')
    f.footer('測られる側に境界がないことと、測る側の物差しが曲がっていることは、別の原因。')
    made.add(f.save('04-b-isotropy-anisotropy.svg'))

    # 05-a sea and summer
    f = Figure(5, '関係もまた、ぼやけた縁を持つ分布', '「海」と「夏」の重なりに、それ自体が意味の雲として関係が立ち上がる', 600, 'a')
    f.blob(470, 380, 160, TEAL); f.blob(730, 380, 160, TERRA)
    f.text(400, 388, '海', 34, TEAL, anchor='middle', weight=700); f.text(800, 388, '夏', 34, TERRA, anchor='middle', weight=700)
    f.text(600, 345, '海水浴', 20, INK, anchor='middle', weight=700); f.text(600, 372, '日焼け・花火の帰り道', 15, INK, anchor='middle'); f.text(600, 395, '潮の匂い・青い色', 15, INK, anchor='middle'); f.text(600, 420, '…', 15, MUTED, anchor='middle')
    f.text(600, 530, '関係は意味であり、意味は分布である。ゆえに関係も分布', 20, INK, anchor='middle', weight=700)
    f.footer('')
    made.add(f.save('05-a-sea-and-summer.svg'))

    # 05-b osaka kyoto kansai
    f = Figure(5, '「間にある」と「中にある」は両立する', 'どの範囲を一塊と見るかの違いに過ぎない', 500, 'b')
    f.panel(180, 215, 840, 220, '')
    f.text(600, 250, '関西', 24, MUTED, anchor='middle', weight=700)
    f.circ(290, 340, 13, INDIGO); f.circ(910, 340, 13, INDIGO)
    f.text(290, 385, '大阪', 20, INK, anchor='middle'); f.text(910, 385, '京都', 20, INK, anchor='middle')
    f.line(306, 340, 894, 340, color=INDIGO, width=2, dash=True)
    for x, nm in [(480, '高槻'), (600, '淀川'), (720, '山崎')]:
        f.circ(x, 340, 7, TERRA); f.text(x, 318, nm, 15, TERRA, anchor='middle')
    f.text(600, 410, '大阪と京都の「間にある」 ＝ 関西の「中にある」', 18, INK, anchor='middle')
    f.text(600, 470, 'ズームを引けば中、寄せれば間', 18, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('05-b-osaka-kyoto-kansai.svg'))

    # 05-c flat paper vs hyperbolic
    f = Figure(5, '平らな紙に木は描けない。双曲空間なら描ける', '枝分かれで先端は何倍にも増えるが、紙の上の場所は距離に比例してしか増えない', 660, 'c')
    f.panel(60, 205, 520, 400, '平らな紙：葉が押し込まれる')
    radial_tree(f, 320, 420, (40, 78, 112), 9, (INDIGO, TEAL, TERRA), leaf_r=(4, 4, 9), spread_deg=(0.4, 0.22, 0.14))
    f.text(320, 585, '遠い枝の葉同士が、紙の上では隣り合ってしまう', 15, INK, anchor='middle')
    f.panel(620, 205, 520, 400, '双曲空間：外へ向かうほど場所が増える')
    radial_tree(f, 880, 410, (28, 70, 150), 9, (INDIGO, TEAL, TERRA), leaf_r=(4, 3.5, 4), spread_deg=(0.4, 0.22, 0.09))
    f.text(880, 588, '中心＝抽象、縁＝具体。近いことと包含されることが同時に成り立つ', 14, INK, anchor='middle')
    f.footer('')
    made.add(f.save('05-c-flat-paper-vs-hyperbolic.svg'))

    # 05-d family resemblance (new)
    f = Figure(5, '家族的類似：全員に共通する一つの特徴はない', '隣り合うものだけが部分的に似ていて、それでも家族だと分かる', 620, 'd')
    for i, (nm, c) in enumerate([('A', INDIGO), ('B', TEAL), ('C', TERRA), ('D', MUTED)]):
        x = 230 + i * 190
        f.circ(x, 380, 110, c, fill=False, width=3)
        f.text(x, 388, nm, 30, c, anchor='middle', weight=700)
    for i, feat in enumerate(['目', '鼻', '輪郭']):
        x = 325 + i * 190
        f.text(x, 388, feat, 18, INK, anchor='middle', weight=700)
        f.text(x, 410, '似ている', 13, MUTED, anchor='middle')
    f.text(515, 540, 'AとDは直接は似ていない。それでも、ひとつながりの家族', 18, INK, anchor='middle')
    f.panel(880, 215, 260, 370, '「鳥」の枝の中で')
    f.circ(1010, 300, 7, INDIGO); f.text(1010, 282, '鳥', 18, INDIGO, anchor='middle', weight=700)
    f.line(1010, 307, 950, 380, color=INDIGO, width=1.5); f.line(1010, 307, 1070, 470, color=INDIGO, width=1.5)
    f.circ(950, 380, 6, TEAL); f.text(950, 405, 'スズメ：近い', 15, TEAL, anchor='middle')
    f.circ(1070, 470, 6, TERRA); f.text(1070, 495, 'ペンギン：遠い', 15, TERRA, anchor='middle')
    f.text(1010, 555, '同じ枝の中。距離が違う', 14, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('05-d-family-resemblance.svg'))

    # 06-a three stages
    f = Figure(6, '「関係なさそう」には、時間の指標が隠れている', 'AとBの間に何があるかを問うとき、関係は見出されるものになる', 560, 'a')
    f.blob(230, 340, 95, INDIGO); f.blob(530, 340, 95, TEAL)
    f.text(230, 345, 'A', 30, INDIGO, anchor='middle', weight=700); f.text(530, 345, 'B', 30, TEAL, anchor='middle', weight=700)
    f.text(380, 352, '？', 42, TERRA, anchor='middle', weight=700)
    f.text(380, 405, '間には何がありますか', 17, MUTED, anchor='middle')
    f.text(880, 240, '「関係なさそう」の三つの段階', 21, INK, anchor='middle', weight=700)
    for i, s in enumerate(['一見、関係なさそう', '「現時点では」関係なさそう', 'まだ関係を発見できていない', 'これから関係していく']):
        y = 275 + i * 44
        f.circ(720, y + 6, 7, TERRA if i < 3 else TEAL)
        f.text(742, y + 12, s, 19, INK)
        if i < 3:
            f.line(720, y + 15, 720, y + 42, color=LINE, width=2)
    f.text(880, 480, '関係は、時間の中で現れる', 18, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('06-a-three-stages.svg'))

    # 06-b hypothesis and verification
    f = Figure(6, '関連は仮説に過ぎない', '見出すことと検証することは別の行為。検証を経て、二つの行き先に分かれる', 560, 'b')
    f.box(430, 215, 340, 80, '関係を見出す', '＝ 仮説', INDIGO, 24)
    f.line(600, 300, 600, 350, color=MUTED, width=2, arrow=True)
    f.text(640, 332, '行動による検証', 17, MUTED)
    f.line(600, 352, 330, 400, color=TEAL, width=2, arrow=True); f.line(600, 352, 870, 400, color=TERRA, width=2, arrow=True)
    f.box(120, 405, 430, 110, '検証された', 'ゴボウの実 → 面ファスナー：何年もの試作を経て', TEAL, 24)
    f.box(650, 405, 430, 110, '検証で消えた', '血液型 → 性格：信じられ、行動されたが、支持されず', TERRA, 24, dash=True)
    f.footer('')
    made.add(f.save('06-b-hypothesis-and-verification.svg'))

    # 07-a two hop
    f = Figure(7, '直接つながっていなくても、共通の媒介を介して結ばれる', '2ホップリンク。媒介が重なるほど、関係は太くなる', 620, 'a')
    f.circ(250, 400, 16, INDIGO); f.text(250, 445, '和歌山', 20, INK, anchor='middle', weight=700)
    f.circ(950, 400, 16, INDIGO); f.text(950, 445, '愛媛', 20, INK, anchor='middle', weight=700)
    f.circ(600, 260, 18, TERRA); f.text(600, 235, 'みかん', 22, TERRA, anchor='middle', weight=700)
    f.line(265, 392, 583, 270, color=TERRA, width=3); f.line(935, 392, 617, 270, color=TERRA, width=3)
    for y, nm in [(335, '温暖な気候'), (470, '海に面している'), (540, '巡礼の文化')]:
        f.circ(600, y, 7, TEAL); f.text(600, y - 14 if y < 400 else y + 26, nm, 14, TEAL, anchor='middle')
        f.line(264, 400, 594, y, color=TEAL, width=1.2); f.line(936, 400, 606, y, color=TEAL, width=1.2)
    f.line(270, 400, 930, 400, color=INDIGO, width=2, dash=True)
    f.text(600, 418, '直接の線はない。それでも意味がある', 14, MUTED, anchor='middle')
    f.footer('太い線が2ホップ。細い線は重なる他の媒介。')
    made.add(f.save('07-a-two-hop.svg'))

    # 07-b surroundings
    f = Figure(7, '周囲が中心を浮かび上がらせる', '言葉にできないXの周囲を明確にしていくと、Xの輪郭が周囲から決まる', 560, 'b')
    f.circ(600, 380, 52, INDIGO, fill=False, dash=True); f.text(600, 390, 'X', 32, INDIGO, anchor='middle', weight=700)
    f.text(600, 452, '名前が出てこない俳優', 15, MUTED, anchor='middle')
    for ang, nm in [(-2.5, '刑事ドラマに出ていた'), (-0.65, 'あの女優と共演'), (0.55, '関西の出身'), (2.55, '昔はお笑い')]:
        x, y = 600 + 240 * math.cos(ang), 380 + 125 * math.sin(ang)
        f.circ(x, y, 9, TERRA)
        ex, ey = 600 + 62 * math.cos(ang), 380 + 62 * math.sin(ang)
        f.line(x, y, ex, ey, color=TERRA, width=1.5, arrow=True)
        f.text(x, y + (-18 if math.sin(ang) < 0 else 30), nm, 16, INK, anchor='middle')
    f.footer('')
    made.add(f.save('07-b-surroundings.svg'))

    # 08-a funnel
    f = Figure(8, '生成は安く、評価は高い', '組み合わせは爆発するが、価値あるものは指数的に少ない', 560, 'a')
    f.text(190, 235, '要素 100', 20, INK, anchor='middle', weight=700)
    for i in range(100):
        f.circ(110 + (i % 10) * 18, 265 + (i // 10) * 18, 4, INDIGO)
    f.line(300, 345, 380, 345, color=MUTED, width=2, arrow=True)
    f.text(340, 325, '組み合わせる', 15, MUTED, anchor='middle'); f.text(340, 372, '安い', 17, TEAL, anchor='middle', weight=700)
    f.text(560, 235, '候補 ～100万', 20, INK, anchor='middle', weight=700)
    for x, y in spread(560, 345, 95, 260, 3):
        f.circ(x, y, 2.6, INDIGO)
    f.body.append(f'<path d="M 690 265 L 760 335 L 760 355 L 690 425 Z" fill="{SOFT}" stroke="{TERRA}" stroke-width="2"/>')
    f.text(725, 240, '評価', 20, TERRA, anchor='middle', weight=700); f.text(725, 462, '高い', 17, TERRA, anchor='middle', weight=700)
    f.line(765, 345, 830, 345, color=MUTED, width=2, arrow=True)
    f.text(960, 235, '価値あるもの', 20, INK, anchor='middle', weight=700)
    for x, y in [(930, 330), (975, 365), (1000, 320)]:
        f.circ(x, y, 9, TERRA)
    f.text(960, 420, '見抜く目の解像度が', 16, MUTED, anchor='middle'); f.text(960, 442, 'ボトルネック', 16, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('08-a-funnel.svg'))

    # 08-b steal ratio
    f = Figure(8, '何作品から、何パーセントずつ盗るか', '源が増えるほど、元の作品は見えなくなる', 440, 'b')
    for i, (n, pct, c, k) in enumerate([('1 作品から', '100% → パクリ', TERRA, 1), ('100 作品から 1% ずつ', 'ほぼオリジナル', INDIGO, 10), ('10000 作品から 0.01% ずつ', '元が分からなくなる', TEAL, 40)]):
        x = 110 + i * 360
        f.text(x, 245, n, 19, c, weight=700); f.text(x, 275, pct, 16, MUTED)
        for j in range(k):
            w = 300 / k
            f.body.append(f'<rect x="{x + j * w:.1f}" y="300" width="{max(w - 2, 2):.1f}" height="44" rx="3" fill="{c}" opacity="{0.9 if k == 1 else 0.55}"/>')
    f.footer('')
    made.add(f.save('08-b-steal-ratio.svg'))

    # 08-c copy vs select (new)
    f = Figure(8, 'パクリと「格好良い」の違いは、選んだかどうか', '一つの源から構造ごと持ってくるか、多数の源から選び抜いて新しい関係に置くか', 690, 'c')
    f.panel(60, 205, 500, 400, 'パクリ：一つの源から構造ごと')
    f.body.append(f'<rect x="110" y="290" width="150" height="150" rx="10" fill="#ffffff" stroke="{TERRA}" stroke-width="2"/>')
    for j in range(4):
        f.body.append(f'<rect x="{125 + (j % 2) * 65}" y="{305 + (j // 2) * 65}" width="55" height="55" rx="6" fill="{TERRA}" opacity="{0.3 + 0.15 * j:.2f}"/>')
    f.text(185, 470, '元の作品', 16, MUTED, anchor='middle')
    f.line(280, 365, 350, 365, color=MUTED, width=2, arrow=True); f.text(315, 350, '複製', 14, MUTED, anchor='middle')
    f.body.append(f'<rect x="360" y="290" width="150" height="150" rx="10" fill="#ffffff" stroke="{TERRA}" stroke-width="2" stroke-dasharray="6 5"/>')
    for j in range(4):
        f.body.append(f'<rect x="{375 + (j % 2) * 65}" y="{305 + (j // 2) * 65}" width="55" height="55" rx="6" fill="{TERRA}" opacity="{0.3 + 0.15 * j:.2f}"/>')
    f.text(435, 470, '元がそのまま透ける', 16, MUTED, anchor='middle')
    f.text(310, 560, '評価は働いていない。媒介が一つしかない2ホップ', 15, INK, anchor='middle')
    f.panel(620, 205, 520, 400, '格好良い：多数の源から選び抜く')
    cols = [INDIGO, TEAL, TERRA, MUTED, '#8a6fd1']
    picks = []
    for i, c in enumerate(cols):
        x, y = 665 + i * 60, 300
        f.body.append(f'<rect x="{x}" y="{y}" width="48" height="48" rx="6" fill="#ffffff" stroke="{c}" stroke-width="2"/>')
        px, py = x + 8 + (i % 2) * 20, y + 8 + ((i * 3) % 2) * 20
        f.body.append(f'<rect x="{px}" y="{py}" width="14" height="14" rx="3" fill="{c}"/>')
        picks.append((px + 7, py + 7, c))
    f.text(785, 375, '多数の源。それぞれの一番良いところだけを選ぶ', 14, MUTED, anchor='middle')
    nx, ny = 1040, 440
    f.circ(nx, ny, 10, INK)
    f.text(nx, 480, '新しい媒介', 14, INK, anchor='middle')
    for i, (px, py, c) in enumerate(picks):
        f.line(px, py + 10, nx - 30 + i * 10, ny - 14, color=c, width=1.5, arrow=True)
    f.text(880, 560, '選び抜く ＝ 評価。要素は元の文脈を離れ、新しい関係の中に入る', 15, INK, anchor='middle')
    f.footer('差は、盗んだ量ではなく、評価した量。')
    made.add(f.save('08-c-copy-vs-select.svg'))

    # 09-a A, B or C
    f = Figure(9, 'A か B か、ではなく「A、B or C」', 'せめぎ合いの間隙からふいに現れる第三のものが、AとBの関係を読み替える', 640, 'a')
    f.blob(470, 440, 150, INDIGO); f.blob(730, 440, 150, TEAL)
    f.text(400, 445, '紙', 32, INDIGO, anchor='middle', weight=700); f.text(800, 445, '画面', 32, TEAL, anchor='middle', weight=700)
    f.text(400, 480, '目に優しい・手触り', 14, MUTED, anchor='middle'); f.text(800, 480, '何千冊・検索', 14, MUTED, anchor='middle')
    f.line(520, 440, 565, 440, color=INDIGO, width=3, arrow=True); f.line(680, 440, 635, 440, color=TEAL, width=3, arrow=True)
    f.path('M 600 400 L 600 300', color=TERRA, width=3, arrow=True)
    f.body.append(f'<polygon points="600,215 610,250 647,255 617,278 625,315 600,297 575,315 583,278 553,255 590,250" fill="{TERRA}" opacity="0.9"/>')
    f.text(600, 195, 'or C：電子ペーパー', 22, TERRA, anchor='middle', weight=700)
    f.text(600, 585, '紙であり、画面である。矛盾がそのまま魅力になる', 18, INK, anchor='middle', weight=700)
    f.text(600, 612, '間隙は一瞬しか開かない。取り出しが遅いとCは消える', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('09-a-a-b-or-c.svg'))

    # 09-b metaphor overlay
    f = Figure(9, '比喩は、二つの分布を強制的に重ねる装置', '直喩は距離を残し、隠喩はゼロにし、擬人法は人間という分布を重ねる', 600, 'b')
    f.panel(60, 205, 340, 340, '直喩：距離を残す')
    f.blob(160, 390, 70, INDIGO); f.blob(300, 390, 70, TERRA)
    f.text(160, 395, '市場', 18, INDIGO, anchor='middle', weight=700); f.text(300, 395, '熊', 18, TERRA, anchor='middle', weight=700)
    f.text(230, 480, '「市場は熊のようだ」', 17, INK, anchor='middle')
    f.panel(430, 205, 340, 340, '隠喩：距離をゼロに')
    f.blob(570, 390, 80, INDIGO); f.blob(630, 390, 80, TERRA)
    f.text(545, 395, '市場', 18, INDIGO, anchor='middle', weight=700); f.text(655, 395, '熊', 18, TERRA, anchor='middle', weight=700)
    f.text(600, 480, '「市場は熊だ」', 17, INK, anchor='middle')
    f.panel(800, 205, 340, 340, '擬人法：人間を重ねる')
    f.blob(950, 390, 85, TEAL); f.blob(990, 390, 85, TERRA)
    f.text(925, 395, '風', 18, TEAL, anchor='middle', weight=700); f.text(1015, 395, '人', 18, TERRA, anchor='middle', weight=700)
    f.text(970, 480, '「風がささやく」', 17, INK, anchor='middle')
    f.text(600, 570, '型は違っても、重ねた瞬間に間に何かが立ち上がる。新しい関連の仮説が生成される', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('09-b-metaphor-overlay.svg'))

    # 10-a same mechanism
    f = Figure(10, '生成の中に、事実と虚構を分けるものはない', '同じ一文、同じ機構。差は後段の検証レイヤーの有無だけ', 600, 'a')
    f.box(70, 330, 300, 100, '生成', '確率的に次の語を選ぶ', INDIGO, 24)
    f.line(375, 380, 440, 380, color=MUTED, width=2, arrow=True)
    f.body.append(f'<rect x="445" y="335" width="330" height="90" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>')
    f.text(610, 372, '「1890年、ロンドンに', 19, INK, anchor='middle'); f.text(610, 400, '一人の探偵が住んでいた」', 19, INK, anchor='middle')
    f.path('M 775 360 C 820 360 820 250 860 250', color=TERRA, width=2, arrow=True)
    f.path('M 775 400 C 820 400 820 520 860 520', color=TEAL, width=2, arrow=True)
    f.box(865, 205, 265, 90, '検証レイヤー', '外部の事実と照合', TERRA, 21)
    f.line(997, 300, 997, 325, color=MUTED, width=1.5)
    f.line(997, 325, 930, 345, color=MUTED, width=1.5, arrow=True); f.line(997, 325, 1064, 345, color=MUTED, width=1.5, arrow=True)
    f.text(915, 380, '一致', 16, TEAL, anchor='middle', weight=700); f.text(915, 404, '事実', 19, INK, anchor='middle', weight=700)
    f.text(1080, 380, '不一致', 16, TERRA, anchor='middle', weight=700); f.text(1080, 404, 'ハルシネーション', 19, INK, anchor='middle', weight=700)
    f.body.append(f'<rect x="865" y="475" width="265" height="90" rx="12" fill="none" stroke="{TEAL}" stroke-width="2" stroke-dasharray="8 7"/>')
    f.text(997, 512, '検証なし', 21, TEAL, anchor='middle', weight=700); f.text(997, 542, '→ 創作として読まれる', 17, MUTED, anchor='middle')
    f.text(610, 470, '文は一字も変わっていない。変わったのは外側だけ', 17, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('10-a-same-mechanism.svg'))

    # 10-b memory
    f = Figure(10, '記憶も同じ形をしている', '思い出すことと作り出すことは、脳の中では同じ動作', 600, 'b')
    f.box(70, 330, 300, 100, '思い出す', '＝ 生成', INDIGO, 24)
    f.line(375, 380, 440, 380, color=MUTED, width=2, arrow=True)
    f.body.append(f'<rect x="445" y="335" width="330" height="90" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>')
    f.text(610, 372, '「あのとき、こう言い返した」', 19, INK, anchor='middle'); f.text(610, 400, 'という記憶', 19, INK, anchor='middle')
    f.path('M 775 360 C 820 360 820 250 860 250', color=TERRA, width=2, arrow=True)
    f.path('M 775 400 C 820 400 820 520 860 520', color=TEAL, width=2, arrow=True)
    f.box(865, 205, 265, 90, '照合', '日記・写真・他人の証言', TERRA, 21)
    f.line(997, 300, 997, 325, color=MUTED, width=1.5)
    f.line(997, 325, 930, 345, color=MUTED, width=1.5, arrow=True); f.line(997, 325, 1064, 345, color=MUTED, width=1.5, arrow=True)
    f.text(915, 380, '一致', 16, TEAL, anchor='middle', weight=700); f.text(915, 404, '本当にあった', 19, INK, anchor='middle', weight=700)
    f.text(1080, 380, '不一致', 16, TERRA, anchor='middle', weight=700); f.text(1080, 404, '作られた記憶', 19, INK, anchor='middle', weight=700)
    f.body.append(f'<rect x="865" y="475" width="265" height="90" rx="12" fill="none" stroke="{TEAL}" stroke-width="2" stroke-dasharray="8 7"/>')
    f.text(997, 512, '照合なし', 21, TEAL, anchor='middle', weight=700); f.text(997, 542, '→ 仮説のまま信じられる', 17, MUTED, anchor='middle')
    f.text(610, 470, '鮮明さは、本当にあったことの証拠にならない', 17, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('10-b-memory.svg'))

    # 10-c evaluation and verification (new)
    f = Figure(10, '評価と検証は、同じ位置にある同じ行為', '後段の箱だけが違う。基準は「価値があるか」と「現実と一致するか」', 610, 'c')
    pipeline(f, 240, '生成', '候補の組み合わせ', '評価', '価値があるか', '採用', '捨てる')
    pipeline(f, 400, '生成', '出力された一文', '検証', '現実と一致するか', '事実', 'ハルシネーション')
    f.text(190, 215, '第8回：創造性', 17, INDIGO, weight=700)
    f.text(190, 375, '第10回：ハルシネーション', 17, INDIGO, weight=700)
    f.body.append(f'<rect x="650" y="222" width="280" height="282" rx="16" fill="none" stroke="{TERRA}" stroke-width="2" stroke-dasharray="7 7"/>')
    f.text(790, 540, '違うのは、この箱の中の基準だけ', 16, TERRA, anchor='middle', weight=700)
    f.footer('生成は安い。評価も検証も、高い。')
    made.add(f.save('10-c-evaluation-and-verification.svg'))

    # 11-a pot and handle
    f = Figure(11, '言葉は、意味を掴んで動かすための取っ手', '鍋そのものは持てない。取っ手を握れば、中身がまるごと動く', 600, 'a')
    f.blob(600, 420, 135, INDIGO, 0.5)
    f.text(600, 415, '意味', 28, INDIGO, anchor='middle', weight=700); f.text(600, 444, 'ぼやけた縁を持つ分布', 15, MUTED, anchor='middle')
    f.body.append(f'<rect x="440" y="245" width="320" height="38" rx="19" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    f.text(600, 271, '言葉（取っ手）', 20, TERRA, anchor='middle', weight=700)
    f.line(600, 283, 600, 300, color=TERRA, width=3)
    f.text(300, 420, '「鳥」と握れば', 18, INK, anchor='end'); f.text(300, 446, 'スズメからペンギンまでが', 15, MUTED, anchor='end'); f.text(300, 468, 'まるごと持ち上がる', 15, MUTED, anchor='end')
    f.text(900, 420, '縁を確定させる必要はない', 18, INK); f.text(900, 446, '別の雲の隣に置けば', 15, MUTED); f.text(900, 468, '間に何かが立ち上がる', 15, MUTED)
    f.footer('')
    made.add(f.save('11-a-pot-and-handle.svg'))

    # 11-b human vs llm
    f = Figure(11, '人間は鍋を持ち、LLMは取っ手だけを直接扱う', '現実の順序が逆である。弱点であり、可能性でもある', 700, 'b')
    f.panel(60, 205, 520, 420, '人間：鍋に取っ手がついている')
    f.blob(300, 450, 125, INDIGO, 0.5)
    f.text(300, 445, '意味', 26, INDIGO, anchor='middle', weight=700); f.text(300, 472, '体験に根ざした分布', 15, MUTED, anchor='middle')
    f.body.append(f'<rect x="150" y="300" width="300" height="34" rx="17" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    f.text(300, 324, '言葉（取っ手）', 19, TERRA, anchor='middle', weight=700)
    f.line(300, 334, 300, 345, color=TERRA, width=3)
    f.text(300, 590, '物理世界が一次、言葉は二次。切れたら体験まで降りて結び直せる', 14, MUTED, anchor='middle')
    f.panel(620, 205, 520, 420, 'LLM：取っ手だけが結び合っている')
    hs = [(760, 330), (900, 300), (1030, 350), (720, 440), (870, 420), (1010, 470), (800, 540), (950, 560)]
    for i, (x, y) in enumerate(hs):
        for j, (x2, y2) in enumerate(hs):
            if j > i and math.hypot(x - x2, y - y2) < 170:
                f.line(x, y, x2, y2, color=LINE, width=1.5)
    for x, y in hs:
        f.body.append(f'<rect x="{x-45}" y="{y-13}" width="90" height="26" rx="13" fill="#ffffff" stroke="{TERRA}" stroke-width="2.5"/>')
        f.text(x, y + 6, '言葉', 14, TERRA, anchor='middle', weight=700)
    f.text(880, 600, '鍋はない。言語そのものが一次的な現実', 15, MUTED, anchor='middle')
    f.footer('弱点：体験まで降りて結び直せない。可能性：取っ手を介さず、言葉そのものの空間を直接動かせる。')
    made.add(f.save('11-b-human-vs-llm.svg'))

    # 12-a loop
    f = Figure(12, '関連は仮説であり、評価がそれを検証する', '見出す → 言葉に固定する → 検証する → 世界の側に置かれる、という循環', 720, 'a')
    f.box(90, 240, 330, 95, '見出す', '2ホップ・比喩・組み合わせ', INDIGO)
    f.box(780, 240, 330, 95, '言葉に固定する', '取っ手をつける・断片を先に置く', INDIGO)
    f.box(780, 480, 330, 95, '検証する', '評価の目・外部の事実と照合', TERRA)
    f.box(90, 480, 330, 95, '世界の側に置かれる', '関係が「ある」と言えるようになる', TEAL)
    f.line(425, 287, 775, 287, color=MUTED, width=2, arrow=True)
    f.line(945, 340, 945, 475, color=MUTED, width=2, arrow=True)
    f.line(775, 527, 425, 527, color=MUTED, width=2, arrow=True)
    f.line(255, 475, 255, 340, color=MUTED, width=2, arrow=True)
    f.text(600, 272, '生成は安い', 18, TEAL, anchor='middle', weight=700)
    f.text(985, 412, '評価は高い', 18, TERRA, anchor='middle')
    f.text(600, 560, '仮説が本物になる', 16, MUTED, anchor='middle')
    f.text(225, 412, '新しい媒介が増え、', 15, MUTED, anchor='end'); f.text(225, 434, '次の関係が見出される', 15, MUTED, anchor='end')
    f.text(600, 400, '関連は仮説に過ぎない', 30, INDIGO, anchor='middle', weight=700)
    f.text(600, 436, '見出すだけでは足りず、言葉にするだけでも足りない', 16, MUTED, anchor='middle')
    f.text(600, 648, '評価の目は、どこから来るのか。', 24, INK, anchor='middle', weight=700)
    f.footer('次の問い：「面白い」と感じる力は、体験という鍋からしか汲めないのか。')
    made.add(f.save('12-a-loop.svg'))

    draw_relation(made)
    draw_openers(made)
    missing, extra = expected - made, made - expected
    if missing or extra:
        raise SystemExit(f'series.json mismatch. missing={sorted(missing)} extra={sorted(extra)}')
    for stale in OUT.rglob('*.svg'):
        if str(stale.relative_to(OUT)) not in made:
            stale.unlink()
    print(f'Generated {len(made)} SVG files in {OUT}')


# ---------------------------------------------------------------------------
# Series 2: RELATION (teal as the primary colour, indigo marks series-1 references)
# ---------------------------------------------------------------------------
R_CODE, R_SUB = 'RELATION', 'relation'
P = TEAL  # primary for series 2


def rfig(number, title, subtitle, height=680, part='a'):
    return Figure(number, title, subtitle, height, part, code=R_CODE, accent=P, subdir=R_SUB)


def person(f, x, y, color=P, label=''):
    f.circ(x, y - 22, 11, color)
    f.path(f'M {x-16} {y+22} C {x-16} {y-4} {x+16} {y-4} {x+16} {y+22} Z', color=color, width=2, fill='#ffffff')
    if label:
        f.text(x, y + 46, label, 15, INK, anchor='middle')


def running_example(f, version: int):
    """The growing figure: same composition in v1..v4, more elements each time."""
    gx, rx, by, bw, bh = 140, 760, 330, 300, 100
    f.box(gx, by, bw, bh, 'AIの生成', '速さを受け持つ', P, 26)
    f.box(rx, by, bw, bh, '人間のレビュー', '正しさを受け持つ', TERRA, 26)
    mid = (gx + bw + rx) / 2
    # v1: three arrows
    f.line(gx + bw + 5, by + 30, rx - 5, by + 30, color=INK, width=2.5, arrow=True)
    f.text(mid, by + 20, '順序：生成が先、レビューが後', 15, INK, anchor='middle')
    f.line(rx - 5, by + 70, gx + bw + 5, by + 70, color=MUTED, width=2, arrow=True, dash=True)
    f.text(mid, by + 92, '依存：レビューは生成がなければ始まらない', 14, MUTED, anchor='middle')
    f.path(f'M {gx+40} {by+bh+12} L {gx+40} {by+bh+30} L {rx+bw-40} {by+bh+30} L {rx+bw-40} {by+bh+12}', color=P, width=2)
    f.text(mid, by + bh + 52, '補完：速さと正しさを分け持つ', 15, P, anchor='middle', weight=700)
    if version == 1:
        f.text(mid, 250, 'この余白は、回を追うごとに埋まっていく', 15, MUTED, anchor='middle')
        f.text(mid, 560, 'どれも「どうつながっているか」の表面しか述べていない', 15, MUTED, anchor='middle')
        return
    # v2: purpose frame, shared resource, substitution ranges, division of labour
    f.panel(gx, 205, rx + bw - gx, 70, '')
    f.text(mid, 248, '目的：正しいコードを速く届ける', 20, INK, anchor='middle', weight=700)
    f.line(gx + bw / 2, by - 4, gx + bw / 2, 278, color=P, width=1.5, arrow=True)
    f.line(rx + bw / 2, by - 4, rx + bw / 2, 278, color=TERRA, width=1.5, arrow=True)
    f.text(mid, by + 42, '分業：AIが作り、人が確かめる', 13, MUTED, anchor='middle')
    cy = by + bh + 120
    f.circ(mid, cy, 30, '#e8c86a')
    f.text(mid, cy + 6, '時間', 15, INK, anchor='middle', weight=700)
    f.text(mid, cy + 52, '資源：人間の時間は一つ。競合', 15, TERRA, anchor='middle', weight=700)
    f.line(gx + bw / 2, by + bh + 36, mid - 34, cy - 10, color=TERRA, width=1.5, arrow=True)
    f.line(rx + bw / 2, by + bh + 36, mid + 34, cy - 10, color=TERRA, width=1.5, arrow=True)
    f.text(gx + 10, by + bh + 80, '「コードを書く」の範囲では代替', 13, MUTED)
    f.text(gx + 10, by + bh + 100, '「正しいコードを届ける」の範囲では補完', 13, MUTED)
    if version == 2:
        return
    # v3: G and R gauges, queue, threshold, delay, externality, irreversibility
    f.text(gx, by - 14, 'G：生成の速さ', 14, P, weight=700)
    f.body.append(f'<rect x="{gx}" y="{by-8}" width="{bw}" height="5" rx="2" fill="{LINE}"/><rect x="{gx}" y="{by-8}" width="{int(bw*0.85)}" height="5" rx="2" fill="{P}"/>')
    f.text(rx, by - 14, 'R：レビューの処理能力', 14, TERRA, weight=700)
    f.body.append(f'<rect x="{rx}" y="{by-8}" width="{bw}" height="5" rx="2" fill="{LINE}"/><rect x="{rx}" y="{by-8}" width="{int(bw*0.5)}" height="5" rx="2" fill="{TERRA}"/>')
    for i in range(7):
        f.body.append(f'<rect x="{int(mid-98+i*28)}" y="{by+44}" width="22" height="16" rx="3" fill="{TERRA}" opacity="{0.35+0.08*i:.2f}"/>')
    f.text(mid, by + 76 - 20, '', 1)
    f.text(mid, by + 118, '滞留：G が R を越えた分が溜まる。閾値は G = R', 14, TERRA, anchor='middle', weight=700)
    f.circ(mid + 150, by + 52, 12, MUTED, fill=False)
    f.line(mid + 150, by + 52, mid + 150, by + 44, color=MUTED, width=1.5); f.line(mid + 150, by + 52, mid + 156, by + 52, color=MUTED, width=1.5)
    f.text(mid + 150, by + 36, '遅延', 12, MUTED, anchor='middle')
    f.line(rx + bw + 5, by + 50, 1175, by + 50, color=MUTED, width=2, arrow=True, dash=True)
    f.text(1120, by + 36, '外部性：後工程へ', 12, MUTED, anchor='middle')
    f.text(rx + bw / 2, cy + 6, '不可逆：流出した欠陥、失った信頼', 13, TERRA, anchor='middle')
    if version == 3:
        f.text(mid, 640, 'G < R：補完が効き、速いほど速い　／　G > R：関係は同じまま、効能が反転する', 15, INK, anchor='middle', weight=700)
        return
    # v4: four layers band and five design levers
    for i, (nm, c) in enumerate([('価値', INDIGO), ('効能', TERRA), ('作用', P), ('構造', MUTED)]):
        y = 220 + i * 95
        f.body.append(f'<rect x="30" y="{y}" width="70" height="80" rx="8" fill="#ffffff" stroke="{c}" stroke-width="2"/>')
        f.text(65, y + 46, nm, 18, c, anchor='middle', weight=700)
    def lever(n, x, y, s):
        f.circ(x, y, 13, INK); f.text(x, y + 6, str(n), 15, '#ffffff', anchor='middle', weight=700); f.text(x + 20, y + 5, s, 13, INK)
    lever(1, mid - 40, by - 40, '効能：GをR以下に保つ（絞る／Rを上げる）')
    lever(2, gx + bw + 20, by + bh + 74, '構造：戻りの流れを速く（小さく、頻繁に）')
    lever(3, rx + 20, 612, '作用：レビューを検査・承認・学習に分ける')
    lever(4, 1080, by + 90, '外部性を帳簿に')
    lever(5, gx + 20, 612, '価値：ない世界を推定して測る')
    f.text(mid, 672, '五つの案のどれも、箱そのものには手を入れていない。上げているのは、あいだ', 15, INK, anchor='middle', weight=700)


def draw_relation(made: set[str]) -> None:
    # 1-1 three lines
    f = rfig(1, '「みかんでつながっている」は、三本の線だった', '同じ二つの県の間に、性質の違う関係が重なっている', 560, 'a')
    f.circ(250, 400, 16, INDIGO); f.text(250, 445, '和歌山', 20, INK, anchor='middle', weight=700)
    f.circ(950, 400, 16, INDIGO); f.text(950, 445, '愛媛', 20, INK, anchor='middle', weight=700)
    f.circ(600, 245, 12, INDIGO); f.text(600, 225, 'みかん（第1クール第7回）', 15, INDIGO, anchor='middle')
    f.line(265, 392, 590, 252, color=INDIGO, width=1, dash=True); f.line(935, 392, 610, 252, color=INDIGO, width=1, dash=True)
    f.path('M 266 390 C 450 330 750 330 934 390', color=P, width=3); f.text(600, 335, '仲間：どちらも産地（同位）', 15, P, anchor='middle', weight=700)
    f.line(266, 400, 934, 400, color=TERRA, width=3); f.text(600, 392, '競争相手：同じ市場を争う（競合）', 15, TERRA, anchor='middle', weight=700)
    f.path('M 266 410 C 450 470 750 470 934 410', color=MUTED, width=3); f.text(600, 478, '比べられる相手：どちらが甘いか（対比）', 15, MUTED, anchor='middle', weight=700)
    f.footer('関係は一つに決まらない。種類の違う線が、同じ二者の間に重なる。')
    made.add(f.save('01-a-three-lines.svg'))

    # 1-2 roadmap
    f = rfig(1, '四つの階層と、四つの部', '構造・作用・効能・価値を下から順に登る', 600, 'b')
    layers = [('価値', '関係がない状態と比べて何が変わるか', INDIGO, '第III部 第10回'), ('効能', 'その結果、何が生まれるか', TERRA, '第III部 第8〜9回'), ('作用', '互いに何をしているか', P, '第II部 第4〜7回'), ('構造', 'どうつながっているか', MUTED, '第I部 第1〜3回')]
    for i, (nm, desc, c, part) in enumerate(layers):
        y = 215 + i * 78
        f.body.append(f'<rect x="150" y="{y}" width="560" height="64" rx="10" fill="#ffffff" stroke="{c}" stroke-width="2"/>')
        f.text(190, y + 40, nm, 22, c, weight=700); f.text(280, y + 40, desc, 17, INK)
        f.text(760, y + 40, part, 16, MUTED)
    f.line(120, 520, 120, 215, color=MUTED, width=2, arrow=True); f.text(110, 370, '登る', 14, MUTED, anchor='end')
    f.body.append(f'<rect x="900" y="300" width="240" height="140" rx="12" fill="#ffffff" stroke="{P}" stroke-width="2"/>')
    f.text(1020, 335, '第IV部 第11〜12回', 15, MUTED, anchor='middle'); f.text(1020, 368, '四階層を束ねて', 17, P, anchor='middle', weight=700); f.text(1020, 395, '関係を設計する', 17, P, anchor='middle', weight=700)
    f.footer('問い：どの関係で、何を生み、何と比べて価値があるのか。')
    made.add(f.save('01-b-roadmap.svg'))

    # 1-3 example v1
    f = rfig(1, 'AIの生成 × 人間のレビュー（第1回）', '順序、依存、補完。まだ三語しか言えない', 600, 'c')
    running_example(f, 1); f.footer('')
    made.add(f.save('01-c-example-v1.svg'))

    # 2-1 four axes
    f = rfig(2, '関係の形を記述する四つの軸', '方向・対称性・強度・時間変化', 620, 'a')
    cols = [(60, '方向'), (335, '対称性'), (610, '強度'), (885, '時間変化')]
    for x, nm in cols:
        f.panel(x, 205, 255, 390, nm)
    # 方向
    f.line(90, 290, 280, 290, color=P, width=3, arrow=True); f.text(185, 320, '一方向：手紙', 15, INK, anchor='middle')
    f.line(90, 380, 280, 380, color=P, width=3, arrow=True); f.line(280, 380, 90, 380, color=P, width=3, arrow=True); f.text(185, 410, '双方向：会話', 15, INK, anchor='middle')
    f.line(90, 470, 280, 470, color=P, width=3); f.text(185, 500, '無向：同じ町の出身', 15, INK, anchor='middle')
    # 対称性
    f.circ(390, 300, 10, P); f.circ(540, 300, 10, P); f.line(400, 300, 530, 300, color=P, width=3); f.text(462, 340, '似ている：対称', 15, INK, anchor='middle')
    f.circ(430, 430, 60, P, fill=False); f.circ(430, 430, 18, TERRA); f.text(462, 520, '含む：非対称', 15, INK, anchor='middle')
    # 強度
    f.line(640, 300, 840, 300, color=TERRA, width=7); f.text(740, 335, '強い依存', 15, INK, anchor='middle')
    f.line(640, 430, 840, 430, color=TERRA, width=1.2, dash=True); f.text(740, 465, '弱い相関', 15, INK, anchor='middle')
    f.text(740, 540, '両側で同じとは限らない', 13, MUTED, anchor='middle')
    # 時間変化
    f.line(915, 300, 1115, 300, color=INDIGO, width=3); f.text(1015, 335, '固定：大阪は関西の中', 14, INK, anchor='middle')
    f.body.append(f'<polyline points="915,470 955,420 995,450 1035,390 1075,430 1115,410" fill="none" stroke="{INDIGO}" stroke-width="3"/>')
    f.text(1015, 505, '動的：二つの店の競合', 14, INK, anchor='middle')
    f.footer('関係の名前が決まる前に、形は問える。')
    made.add(f.save('02-a-four-axes.svg'))

    # 3-1 summer triangle
    f = rfig(3, 'アイスクリームと水難事故', '向きのない相関の上に、向きのある因果の源がある', 560, 'a')
    f.circ(600, 250, 34, TERRA); f.text(600, 258, '夏', 24, '#ffffff', anchor='middle', weight=700)
    f.circ(320, 460, 30, P); f.text(320, 466, 'アイス', 16, '#ffffff', anchor='middle', weight=700)
    f.circ(880, 460, 30, P); f.text(880, 466, '事故', 16, '#ffffff', anchor='middle', weight=700)
    f.line(575, 275, 345, 438, color=TERRA, width=3, arrow=True); f.line(625, 275, 855, 438, color=TERRA, width=3, arrow=True)
    f.text(430, 345, '因果：暑いから売れる', 15, TERRA, anchor='middle'); f.text(770, 345, '因果：暑いから水辺へ', 15, TERRA, anchor='middle')
    f.line(352, 460, 848, 460, color=MUTED, width=2, dash=True); f.text(600, 490, '相関：一緒に増える。向きはない', 15, MUTED, anchor='middle')
    f.footer('アイスを止めても事故は減らない。見えやすい相関が、見えにくい因果に化ける。')
    made.add(f.save('03-a-summer-triangle.svg'))

    # 3-2 five pairs
    f = rfig(3, '五つの組：見えやすいほうと、確かめにくいほう', '取り違えは、いつも同じ向きに起きる', 640, 'b')
    f.text(420, 215, '見えやすい', 18, P, anchor='middle', weight=700); f.text(820, 215, '確かめにくい', 18, TERRA, anchor='middle', weight=700)
    rows = [('相関', '因果', '夏とアイスと事故'), ('条件（依存）', '原因', '酸素と火'), ('種類として含む', '部品として含む', '犬は動物、エンジンは車'), ('違う（対比）', '両立しない（対立）', '赤と青、一つの椅子'), ('補い合う（補完）', 'なければ成り立たない（依存）', '両手と、鍵と錠')]
    for i, (l, r, ex) in enumerate(rows):
        y = 250 + i * 68
        f.body.append(f'<rect x="250" y="{y}" width="340" height="48" rx="10" fill="#ffffff" stroke="{P}" stroke-width="2"/>'); f.text(420, y + 31, l, 17, INK, anchor='middle', weight=700)
        f.body.append(f'<rect x="650" y="{y}" width="340" height="48" rx="10" fill="#ffffff" stroke="{TERRA}" stroke-width="2" stroke-dasharray="7 6"/>'); f.text(820, y + 31, r, 17, INK, anchor='middle', weight=700)
        f.text(1010, y + 31, ex, 13, MUTED)
        f.line(595, y + 24, 645, y + 24, color=MUTED, width=1.5, arrow=True)
    f.footer('外してみないと分からない。関係がなかったら、どうなるのか（第10回へ）。')
    made.add(f.save('03-b-five-pairs.svg'))

    # 4-1 opposite and dual
    f = rfig(4, '紙と画面は反対。電子ペーパーは双対', '共通の軸の両端と、役割を入れ替えて置いた第三のもの', 580, 'a')
    f.line(200, 430, 1000, 430, color=LINE, width=3); f.text(600, 470, '共通の軸：読むための面', 15, MUTED, anchor='middle')
    f.blob(300, 430, 90, INDIGO); f.text(300, 436, '紙', 26, INDIGO, anchor='middle', weight=700)
    f.blob(900, 430, 90, P); f.text(900, 436, '画面', 26, P, anchor='middle', weight=700)
    f.line(400, 400, 800, 400, color=TERRA, width=2); f.line(800, 400, 400, 400, color=TERRA, width=2, arrow=True); f.text(600, 390, '反対：両端にある。両立する', 15, TERRA, anchor='middle', weight=700)
    f.body.append(f'<rect x="500" y="230" width="200" height="90" rx="12" fill="#ffffff" stroke="{TERRA}" stroke-width="2"/>')
    f.text(600, 268, '電子ペーパー', 19, TERRA, anchor='middle', weight=700); f.text(600, 296, '紙の構造 ＋ 画面の役割', 14, MUTED, anchor='middle')
    f.line(330, 395, 520, 325, color=INDIGO, width=1.5, dash=True); f.text(400, 345, '構造を借りる', 13, INDIGO, anchor='middle')
    f.line(870, 395, 680, 325, color=P, width=1.5, dash=True); f.text(800, 345, '役割を入れ替える', 13, P, anchor='middle')
    f.text(600, 215, '双対：共通の構造の中で役割を入れ替えても対応が保たれる', 14, INK, anchor='middle')
    f.footer('第1クール第9回の「A、B or C」を、関係の名前で言い直す。')
    made.add(f.save('04-a-opposite-and-dual.svg'))

    # 4-2 analogy table
    f = rfig(4, '類比は、対応表を要求する', '血管と道路網。空欄が、類比の限界を教える', 600, 'b')
    f.text(330, 225, '血管', 20, TERRA, anchor='middle', weight=700); f.text(870, 225, '道路網', 20, P, anchor='middle', weight=700)
    pairs = [('血液', '車'), ('心臓', '物流拠点'), ('詰まり', '渋滞'), ('（なし）', '信号')]
    for i, (l, r) in enumerate(pairs):
        y = 260 + i * 72
        empty = l.startswith('（')
        lc = LINE if empty else TERRA
        dl = ' stroke-dasharray="7 6"' if empty else ''
        f.body.append(f'<rect x="200" y="{y}" width="260" height="48" rx="10" fill="#ffffff" stroke="{lc}" stroke-width="2"{dl}/>'); f.text(330, y + 31, l, 17, MUTED if empty else INK, anchor='middle', weight=700)
        f.body.append(f'<rect x="740" y="{y}" width="260" height="48" rx="10" fill="#ffffff" stroke="{P}" stroke-width="2"/>'); f.text(870, y + 31, r, 17, INK, anchor='middle', weight=700)
        if not l.startswith('（'):
            f.line(465, y + 24, 735, y + 24, color=MUTED, width=1.5); f.line(735, y + 24, 465, y + 24, color=MUTED, width=1.5)
        else:
            f.text(600, y + 29, '対応なし ＝ 類比の限界', 14, TERRA, anchor='middle', weight=700)
    f.footer('比喩は表現の関係、類比は構造の関係。類比は仮説を検証可能な形に整える。')
    made.add(f.save('04-b-analogy-table.svg'))

    # 5-1 same two people
    f = rfig(5, '同じ二人が、補完にも競合にもなる', '二人は変わらない。変わったのは、二人を囲む枠', 600, 'a')
    f.panel(80, 205, 500, 360, '目的の枠：プロジェクトの成功')
    person(f, 230, 380, P, '構想に強い'); person(f, 430, 380, TERRA, '細部に強い')
    f.line(255, 380, 405, 380, color=P, width=3, arrow=True); f.line(405, 392, 255, 392, color=TERRA, width=3, arrow=True)
    f.text(330, 520, '補完：構想が細部を導き、細部が構想を現実にする', 14, INK, anchor='middle', weight=700)
    f.panel(620, 205, 500, 360, '資源の枠：席は一つ')
    person(f, 770, 380, P, '構想に強い'); person(f, 970, 380, TERRA, '細部に強い')
    f.body.append(f'<rect x="845" y="300" width="50" height="40" rx="6" fill="#ffffff" stroke="{INK}" stroke-width="2"/>'); f.text(870, 290, '席', 14, INK, anchor='middle')
    f.line(790, 360, 850, 335, color=P, width=2.5, arrow=True); f.line(950, 360, 890, 335, color=TERRA, width=2.5, arrow=True)
    f.text(870, 520, '競合：同じ資源を争う', 14, INK, anchor='middle', weight=700)
    f.footer('機能の関係は、二者の性質ではなく、目的と範囲と資源の枠で決まる。')
    made.add(f.save('05-a-same-two-people.svg'))

    # 5-2 washing machine
    f = rfig(5, '代替か補完かは、どの範囲で見るかの問い', '洗濯機は「洗う」を代替し、「洗濯」の全体では人間を補完する', 540, 'b')
    for i, (nm, c) in enumerate([('洗う', P), ('干す', MUTED), ('畳む', MUTED)]):
        x = 200 + i * 280
        f.body.append(f'<rect x="{x}" y="300" width="240" height="70" rx="10" fill="#ffffff" stroke="{c}" stroke-width="2"/>'); f.text(x + 120, 343, nm, 22, c, anchor='middle', weight=700)
    f.body.append(f'<rect x="210" y="310" width="220" height="50" rx="8" fill="{P}" opacity="0.18"/>'); f.text(320, 290, '洗濯機', 14, P, anchor='middle', weight=700)
    f.path('M 200 260 L 200 245 L 440 245 L 440 260', color=P, width=2); f.text(320, 235, '「洗う」の範囲：洗濯板を代替', 15, P, anchor='middle', weight=700)
    f.path('M 200 400 L 200 418 L 1000 418 L 1000 400', color=TERRA, width=2); f.text(600, 445, '「洗濯」の範囲：干す・畳むは人のまま。人間を補完', 15, TERRA, anchor='middle', weight=700)
    f.footer('「AIは人間を代替するか」に答えが出ないのは、範囲が指定されていないから。')
    made.add(f.save('05-b-washing-machine.svg'))

    # 5-3 example v2
    f = rfig(5, 'AIの生成 × 人間のレビュー（第5回）', '目的の枠、人間の時間という資源、代替の範囲、分業', 620, 'c')
    running_example(f, 2); f.footer('')
    made.add(f.save('05-c-example-v2.svg'))

    # 6-2 two loops (figure 6-1 in the chapter)
    f = rfig(6, '膨らむ輪と、収まる輪', '一周すると、原因と結果の席が入れ替わっている', 600, '2')
    f.panel(80, 205, 500, 360, '正のフィードバック：増幅')
    f.box(130, 300, 160, 60, '褒める', '', P, 20); f.box(370, 300, 160, 60, '伸びる', '', TERRA, 20)
    f.path('M 295 315 L 365 315', color=P, width=2.5, arrow=True); f.path('M 365 345 L 295 345', color=TERRA, width=2.5, arrow=True)
    f.text(330, 290, '原因→結果', 12, P, anchor='middle'); f.text(330, 372, '結果→原因', 12, TERRA, anchor='middle')
    for i, r in enumerate((22, 34, 46)):
        f.circ(330, 460, r, P, fill=False, width=1.5)
    f.text(330, 530, '放っておくと膨らみ続ける', 14, INK, anchor='middle')
    f.panel(620, 205, 500, 360, '負のフィードバック：安定化')
    pts = [('疲れる', 870, 270), ('休む', 1010, 370), ('動く', 730, 370), ('回復する', 870, 470)]
    for nm, x, y in pts:
        f.body.append(f'<rect x="{x-55}" y="{y-20}" width="110" height="40" rx="10" fill="#ffffff" stroke="{TERRA}" stroke-width="2"/>'); f.text(x, y + 6, nm, 15, INK, anchor='middle', weight=700)
    f.path('M 925 280 C 990 300 1010 320 1010 348', color=MUTED, width=2, arrow=True); f.path('M 1000 392 C 980 440 930 465 928 468', color=MUTED, width=2, arrow=True)
    f.path('M 815 468 C 760 450 735 420 732 392', color=MUTED, width=2, arrow=True); f.path('M 735 348 C 745 310 790 285 814 278', color=MUTED, width=2, arrow=True)
    f.text(870, 540, '一定の範囲に収まろうとする', 14, INK, anchor='middle')
    f.footer('どちらが原因かは、どこから見るかで変わる。')
    made.add(f.save('06-a-two-loops.svg'))

    # 7-2 two axes (figure 7-1)
    f = rfig(7, '意味の近さと、構造の似方は別の軸', '意味は遠いが構造は似ている組が、転用の着想源になる', 640, '2')
    ox, oy, w, h = 260, 560, 680, 330
    f.line(ox, oy, ox + w, oy, color=MUTED, width=2, arrow=True); f.text(ox + w / 2, oy + 30, '意味の近さ →', 15, MUTED, anchor='middle')
    f.line(ox, oy, ox, oy - h, color=MUTED, width=2, arrow=True); f.text(ox - 16, oy - h / 2, '構造の似方 ↑', 15, MUTED, anchor='end')
    f.line(ox + w / 2, oy, ox + w / 2, oy - h, color=LINE, width=1, dash=True); f.line(ox, oy - h / 2, ox + w, oy - h / 2, color=LINE, width=1, dash=True)
    f.text(ox + 3 * w / 4, oy - 3 * h / 4, '類義語：驚きはない', 15, MUTED, anchor='middle')
    f.text(ox + w / 4, oy - h / 4, '本当に無関係', 15, MUTED, anchor='middle')
    f.text(ox + 3 * w / 4, oy - h / 4, '意味は近いが、構造は違う', 14, MUTED, anchor='middle')
    f.body.append(f'<rect x="{ox+30}" y="{oy-h+20}" width="{w/2-60}" height="{h/2-40}" rx="12" fill="{P}" opacity="0.12"/>')
    f.text(ox + w / 4, oy - 3 * h / 4 - 14, 'レビュー滞留 ↔ 工場の仕掛品', 16, P, anchor='middle', weight=700)
    f.text(ox + w / 4, oy - 3 * h / 4 + 14, '意味は遠いが、構造は似ている', 14, P, anchor='middle')
    f.text(ox + w / 4, oy - 3 * h / 4 + 36, '＝ 転用の着想源', 14, P, anchor='middle', weight=700)
    f.footer('関係は一つではない。同じ二つの対象が、意味の軸では遠く、構造の軸では近い。')
    made.add(f.save('07-a-two-axes.svg'))

    # 7-3 three readings (figure 7-2)
    f = rfig(7, '「レビュー」の三つの解釈が、三つの関係になる', '解釈が割れると、関係の種類まで割れる', 560, '3')
    f.box(80, 320, 220, 80, '「レビュー」', '一つの言葉', INK, 22)
    rows = [('検査：欠陥を見つける', '補完（第5回）', P), ('承認：通すか止めるか', '制約：ゲート', TERRA), ('学習：読んで学ぶ', '継承：双方向（第6回）', INDIGO)]
    for i, (r, rel, c) in enumerate(rows):
        y = 230 + i * 110
        f.line(305, 360, 395, y + 30, color=c, width=2, arrow=True)
        f.body.append(f'<rect x="400" y="{y}" width="300" height="60" rx="10" fill="#ffffff" stroke="{c}" stroke-width="2"/>'); f.text(550, y + 37, r, 16, INK, anchor='middle', weight=700)
        f.line(705, y + 30, 775, y + 30, color=c, width=2, arrow=True)
        f.body.append(f'<rect x="780" y="{y}" width="320" height="60" rx="10" fill="#ffffff" stroke="{c}" stroke-width="2" stroke-dasharray="7 6"/>'); f.text(940, y + 37, rel, 16, c, anchor='middle', weight=700)
    f.footer('関係について意見が合わないとき、争われているのは言葉の解釈であることが多い。')
    made.add(f.save('07-b-three-readings.svg'))

    # 8-1 type vs effect
    f = rfig(8, '関係の種類と、関係が生むものは、別の束', '相似があっても、条件が揃わなければ転用は起きない', 560, 'a')
    f.body.append(f'<rect x="90" y="280" width="260" height="150" rx="14" fill="#ffffff" stroke="{P}" stroke-width="2.5"/>')
    f.text(220, 318, '相似', 24, P, anchor='middle', weight=700); f.text(220, 348, '関係の型', 14, MUTED, anchor='middle'); f.text(220, 372, '対称・推移しない', 13, MUTED, anchor='middle'); f.text(220, 395, '例：心臓とポンプ', 13, MUTED, anchor='middle')
    f.body.append(f'<rect x="850" y="280" width="260" height="150" rx="14" fill="#ffffff" stroke="{TERRA}" stroke-width="2.5"/>')
    f.text(980, 318, '知識転用', 24, TERRA, anchor='middle', weight=700); f.text(980, 348, '効能の型', 14, MUTED, anchor='middle'); f.text(980, 372, '帰属：転用先', 13, MUTED, anchor='middle'); f.text(980, 395, '例：血液の循環', 13, MUTED, anchor='middle')
    f.panel(420, 255, 360, 200, '条件')
    for i, s in enumerate(['共通する構造が特定されている', '運ぶ知識が手元にある', '運んだ先で成り立つか確かめられる']):
        f.circ(450, 310 + i * 40, 5, INK); f.text(468, 316 + i * 40, s, 14, INK)
    f.line(355, 355, 415, 355, color=MUTED, width=2, arrow=True, dash=True); f.line(785, 355, 845, 355, color=MUTED, width=2, arrow=True, dash=True)
    f.text(600, 490, '点線：生じうるが、保証ではない。多対多の対応', 15, INK, anchor='middle', weight=700)
    f.footer('種類と効能を混同しない。')
    made.add(f.save('08-a-type-vs-effect.svg'))

    # 8-2 attribution
    f = rfig(8, '効能は、どこに帰属するか', '対象への効能、関係そのものへの効能、全体への効能', 650, 'b')
    f.body.append(f'<rect x="200" y="215" width="800" height="340" rx="22" fill="none" stroke="{INDIGO}" stroke-width="2" stroke-dasharray="8 7"/>')
    f.text(600, 250, '全体：家庭の空気', 17, INDIGO, anchor='middle', weight=700)
    f.blob(430, 400, 110, P); f.text(430, 406, '夫', 26, P, anchor='middle', weight=700)
    f.blob(770, 400, 110, TERRA); f.text(770, 406, '妻', 26, TERRA, anchor='middle', weight=700)
    f.line(500, 400, 700, 400, color=INK, width=3); f.text(600, 385, '関係そのもの：信頼', 15, INK, anchor='middle', weight=700)
    f.text(430, 520, '対象への効能：夫の考えが変わる', 13, MUTED, anchor='middle'); f.text(770, 520, '対象への効能：妻の考えが変わる', 13, MUTED, anchor='middle')
    f.text(600, 440, '二人の考えは変わらないのに、間が変わることがある', 13, MUTED, anchor='middle')
    f.footer('どこに帰属するかで、測る場所が変わる。夫の変化を測っても、信頼の変化は見えない。')
    made.add(f.save('08-b-attribution.svg'))

    # 9-1 threshold
    f = rfig(9, '閾値：どこかで符号が反転する', '会議の人数と、結論の質', 580, 'a')
    ox, oy = 180, 480
    f.line(ox, oy, 1060, oy, color=MUTED, width=2, arrow=True); f.text(620, oy + 32, '会議の人数 →', 15, MUTED, anchor='middle')
    f.line(ox, oy, ox, 220, color=MUTED, width=2, arrow=True); f.text(ox - 14, 350, '結論の質 ↑', 15, MUTED, anchor='end')
    pts = []
    for i in range(61):
        x = ox + 20 + i * 14
        n = i / 60
        yv = 1 - ((n - 0.42) * 2.2) ** 2
        pts.append(f'{x:.1f},{oy - 40 - 190 * max(yv, -0.3):.1f}')
    f.body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{P}" stroke-width="3.5"/>')
    tx = ox + 20 + 25 * 14
    f.line(tx, oy, tx, 240, color=TERRA, width=2, dash=True); f.text(tx, 228, '境目', 16, TERRA, anchor='middle', weight=700)
    f.text(tx - 160, 300, '手前：人を増やすほど良い', 14, P, anchor='middle'); f.text(tx + 190, 300, '先：人を増やすほど遅く薄くなる', 14, TERRA, anchor='middle')
    f.text(tx - 160, 322, '効能は正', 14, P, anchor='middle'); f.text(tx + 190, 322, '効能は負', 14, TERRA, anchor='middle')
    f.footer('閾値は参加者の性質ではなく、場の容量で決まる。')
    made.add(f.save('09-a-threshold.svg'))

    # 9-3 example v3 (figure 9-2)
    f = rfig(9, 'AIの生成 × 人間のレビュー（第9回）', 'G と R、滞留、閾値、遅延、外部性、不可逆', 680, '3')
    running_example(f, 3); f.footer('')
    made.add(f.save('09-b-example-v3.svg'))

    # 10-1 two worlds
    f = rfig(10, '価値は、ない世界との差', '純効果から費用を引いて、正味の価値', 600, '2')
    f.panel(80, 205, 440, 300, '関係がある世界')
    f.blob(220, 370, 80, P); f.blob(380, 370, 80, TERRA); f.line(260, 370, 340, 370, color=INK, width=3)
    f.text(300, 470, '観測できる', 14, MUTED, anchor='middle')
    f.panel(680, 205, 440, 300, '関係がない世界')
    f.blob(820, 370, 80, P); f.blob(980, 370, 80, TERRA)
    f.text(900, 470, '観測できない。想像で組み立てる（反実仮想）', 13, MUTED, anchor='middle')
    f.text(600, 360, '−', 44, INK, anchor='middle', weight=700)
    f.path('M 80 530 L 80 548 L 1120 548 L 1120 530', color=INK, width=2)
    f.text(600, 575, '純効果 ＝ ある世界の結果 − ない世界の結果　　正味の価値 ＝ 純効果 − 関係を結び、維持する費用', 15, INK, anchor='middle', weight=700)
    f.footer('')
    made.add(f.save('10-a-two-worlds.svg'))

    # 11-1 card system
    f = rfig(11, 'カードの仕組み', '型と実例、関係の束と効能の束、二つをつなぐ規則、根拠と状態', 700, 'a')
    def card(x, y, w, h, title, lines, c, dash=False):
        da = ' stroke-dasharray="7 6"' if dash else ''
        f.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#ffffff" stroke="{c}" stroke-width="2.5"{da}/>')
        f.text(x + w / 2, y + 30, title, 17, c, anchor='middle', weight=700)
        for i, s in enumerate(lines):
            f.text(x + 14, y + 56 + i * 20, s, 12, INK)
    card(70, 215, 250, 150, '型：相似', ['定義 / 形：対称・推移しない', '成立条件', '生じうる効能'], P)
    card(70, 420, 250, 150, '実例：心臓 × ポンプ', ['型：相似', '根拠：誰が、何を見て', '状態：仮説 → 検証済み'], P, dash=True)
    f.line(195, 370, 195, 415, color=P, width=2, arrow=True); f.text(210, 398, '二者の間に置く', 12, MUTED)
    card(880, 215, 250, 150, '型：知識転用', ['定義 / 帰属：転用先', '価値の向き', ''], TERRA)
    card(880, 420, 250, 150, '実例：血液の循環', ['型：知識転用', '根拠 / 状態', ''], TERRA, dash=True)
    f.line(1005, 370, 1005, 415, color=TERRA, width=2, arrow=True)
    card(430, 290, 340, 200, '規則：相似 → 知識転用', ['仕組み：共通構造を抽出し、対応づける', '前提条件：共通構造が特定されている…', '限界：表面的な類似は保証しない', '状態：仮説'], INK)
    f.line(325, 290, 425, 330, color=MUTED, width=2, arrow=True); f.line(775, 330, 875, 290, color=MUTED, width=2, arrow=True)
    f.text(195, 610, '関係の束', 15, P, anchor='middle', weight=700); f.text(1005, 610, '効能の束', 15, TERRA, anchor='middle', weight=700); f.text(600, 540, '二つの束は、直接つながない', 13, MUTED, anchor='middle')
    f.footer('一組の二者の間に、複数の実例カードを重ねられる。関係は一つではない。')
    made.add(f.save('11-a-card-system.svg'))

    # 11-2 thirteen cards
    f = rfig(11, 'AIの生成 × 人間のレビュー、十三枚のカード', '対象2・関係5・効能4・規則2', 720, 'b')
    def mini(x, y, title, sub, c, dash=False):
        da = ' stroke-dasharray="6 5"' if dash else ''
        f.body.append(f'<rect x="{x}" y="{y}" width="190" height="62" rx="10" fill="#ffffff" stroke="{c}" stroke-width="2"{da}/>')
        f.text(x + 95, y + 26, title, 14, c, anchor='middle', weight=700); f.text(x + 95, y + 48, sub, 11, MUTED, anchor='middle')
    f.text(160, 215, '対象', 15, INK, anchor='middle', weight=700)
    mini(65, 230, 'AIの生成', '', INK); mini(65, 302, '人間のレビュー', '', INK)
    f.text(480, 215, '関係の実例（5）', 15, P, anchor='middle', weight=700)
    for i, (t_, s) in enumerate([('順序', '有向'), ('依存', '非対称：レビュー→生成'), ('補完', '目的：正しいコードを速く'), ('競合', '資源：人間の時間'), ('フィードバック', '待ちが生成へ戻る輪')]):
        mini(385, 230 + i * 72, t_, s, P, dash=True)
    f.text(800, 215, '効能の実例（4）', 15, TERRA, anchor='middle', weight=700)
    for i, (t_, s) in enumerate([('時間の短縮', '正・全体に帰属'), ('欠陥の検出', '正・コードに帰属'), ('滞留', '負・関係そのものに帰属'), ('信頼の変化', '混合・関係そのものに帰属')]):
        mini(705, 230 + i * 72, t_, s, TERRA, dash=True)
    f.text(1030, 215, '規則（2）', 15, INK, anchor='middle', weight=700)
    mini(935, 230, '補完 → 相乗', '前提：G < R　状態：仮説', INK); mini(935, 302, '依存 → 滞留', '前提：G > R　状態：仮説', INK)
    f.text(600, 650, '第1回に三語で書いたものが、ここまで厚くなった。', 16, INK, anchor='middle', weight=700)
    f.footer('')
    made.add(f.save('11-b-thirteen-cards.svg'))


    # 2-2 transitivity
    f = rfig(2, '推移するか、しないか', '「含む」の鎖は端まで通り、「似ている」の鎖は通らない', 640, '2')
    f.panel(60, 205, 1080, 150, '')
    for x, nm in [(230, '大阪'), (600, '関西'), (970, '日本')]:
        f.box(x - 90, 245, 180, 60, nm, '', P, 22)
    f.line(325, 275, 505, 275, color=P, width=2.5, arrow=True); f.text(415, 262, '含まれる', 14, MUTED, anchor='middle')
    f.line(695, 275, 875, 275, color=P, width=2.5, arrow=True); f.text(785, 262, '含まれる', 14, MUTED, anchor='middle')
    f.path('M 230 310 C 230 345 970 345 970 310', color=P, width=2, arrow=True); f.text(600, 345, '推移する：大阪は日本に含まれる', 15, P, anchor='middle', weight=700)
    f.panel(60, 385, 1080, 200, '')
    for x, nm, c in [(230, '父', INDIGO), (600, '子', INK), (970, '母', TERRA)]:
        person(f, x, 470, c, nm)
    f.line(260, 460, 570, 460, color=INDIGO, width=2.5); f.text(415, 448, '目が似ている', 14, INDIGO, anchor='middle')
    f.line(630, 460, 940, 460, color=TERRA, width=2.5); f.text(785, 448, '鼻が似ている', 14, TERRA, anchor='middle')
    f.path('M 230 535 C 230 575 970 575 970 535', color=MUTED, width=2, dash=True); f.text(600, 575, '推移しない：父と母は似ていない', 15, MUTED, anchor='middle', weight=700)
    f.footer('似ているは対称だが推移しない。同じであるは対称で、かつ推移する。')
    made.add(f.save('02-b-transitivity.svg'))

    # 6-1 condition / facilitation / cause
    f = rfig(6, '条件・促進・原因の三段', '「なければ起きない」「あれば起きやすい」「あれば起きる」', 520, '1')
    cols = [(60, '条件（依存）', '種', 'なければ起きない', 0.25, MUTED), (420, '促進', '肥料', 'あれば起きやすい', 0.6, P), (780, '原因', '（原因）', 'あれば起きる', 1.0, TERRA)]
    for x, title, ex, desc, strength, c in cols:
        f.panel(x, 205, 360, 250, title)
        f.text(x + 180, 285, ex, 22, c, anchor='middle', weight=700)
        f.text(x + 180, 318, desc, 16, INK, anchor='middle')
        f.body.append(f'<rect x="{x+60}" y="350" width="240" height="12" rx="6" fill="{LINE}"/><rect x="{x+60}" y="350" width="{int(240*strength)}" height="12" rx="6" fill="{c}"/>')
        f.text(x + 180, 390, '結果への寄与の強さ', 12, MUTED, anchor='middle')
    f.line(430, 300, 410, 300, color=MUTED, width=1.5); f.line(790, 300, 770, 300, color=MUTED, width=1.5)
    f.footer('中間の段は見落とされやすく、原因に格上げされるか、無関係に格下げされがち。')
    made.add(f.save('06-b-condition-spectrum.svg'))

    # 6-3 example loops
    f = rfig(6, 'AIの生成 × 人間のレビュー、二つの輪', '安定させる輪と、膨らませる輪が、同じ二者の間で同時に回りうる', 660, '3')
    f.panel(60, 205, 520, 390, '収まる輪（負のフィードバック）')
    for nm, x, y in [('生成が増える', 320, 265), ('待ちが増える', 470, 380), ('生成が減る', 320, 495), ('待ちが減る', 170, 380)]:
        f.body.append(f'<rect x="{x-70}" y="{y-20}" width="140" height="40" rx="10" fill="#ffffff" stroke="{P}" stroke-width="2"/>'); f.text(x, y + 6, nm, 14, INK, anchor='middle', weight=700)
    f.path('M 392 275 C 450 290 470 330 470 358', color=MUTED, width=2, arrow=True); f.path('M 465 402 C 450 450 400 480 392 486', color=MUTED, width=2, arrow=True)
    f.path('M 248 486 C 200 470 170 440 170 402', color=MUTED, width=2, arrow=True); f.path('M 175 358 C 190 310 240 280 248 275', color=MUTED, width=2, arrow=True)
    f.text(320, 565, 'どこかの水準に落ち着こうとする', 14, INK, anchor='middle')
    f.panel(620, 205, 520, 390, '膨らむ輪（正のフィードバック）')
    for nm, x, y in [('待ちが増える', 880, 265), ('レビューが雑になる', 1030, 380), ('欠陥が流出する', 880, 495), ('手戻りが起きる', 730, 380)]:
        f.body.append(f'<rect x="{x-80}" y="{y-20}" width="160" height="40" rx="10" fill="#ffffff" stroke="{TERRA}" stroke-width="2"/>'); f.text(x, y + 6, nm, 14, INK, anchor='middle', weight=700)
    f.path('M 962 275 C 1010 290 1030 330 1030 358', color=TERRA, width=2, arrow=True); f.path('M 1025 402 C 1010 450 960 480 962 486', color=TERRA, width=2, arrow=True)
    f.path('M 798 486 C 750 470 730 440 730 402', color=TERRA, width=2, arrow=True); f.path('M 735 358 C 750 310 790 280 798 275', color=TERRA, width=2, arrow=True)
    f.text(880, 565, '放っておくと膨らむ', 14, INK, anchor='middle')
    f.footer('どちらの輪が勝つかは、二者の性質ではなく、待ちが越える境目で決まる（第9回）。')
    made.add(f.save('06-c-example-loops.svg'))

    # 7-1 association vs entailment chains
    f = rfig(7, '連想の鎖と、含意の鎖', 'どちらも有向。含意は推移し、連想は推移しない', 600, '1')
    f.text(120, 262, '連想', 20, P, weight=700)
    for x, nm in [(300, '夏'), (600, '海'), (900, '塩')]:
        f.box(x - 70, 235, 140, 56, nm, '', P, 22)
    f.line(375, 263, 525, 263, color=P, width=2.5, arrow=True); f.line(675, 263, 825, 263, color=P, width=2.5, arrow=True)
    f.path('M 300 296 C 300 340 900 340 900 296', color=MUTED, width=2, dash=True); f.text(600, 345, '夏から塩は、ほとんど浮かばない：推移しない', 15, MUTED, anchor='middle', weight=700)
    f.text(120, 432, '含意', 20, TERRA, weight=700)
    for x, nm in [(300, '独身男性'), (600, '未婚'), (900, '配偶者がいない')]:
        f.box(x - 90, 405, 180, 56, nm, '', TERRA, 19)
    f.line(395, 433, 505, 433, color=TERRA, width=2.5, arrow=True); f.line(695, 433, 805, 433, color=TERRA, width=2.5, arrow=True)
    f.path('M 300 466 C 300 505 900 505 900 466', color=TERRA, width=2, arrow=True); f.text(600, 508, '独身男性なら配偶者はいない：推移する', 15, TERRA, anchor='middle', weight=700)
    f.footer('意味の関係の中にも、推移するものとしないものが混ざっている。')
    made.add(f.save('07-c-chains.svg'))

    # 8-3 example effects by attribution
    f = rfig(8, 'AIの生成 × 人間のレビュー、効能の帰属', '直接の効能、間接の効能、関係そのもの、全体', 600, '3')
    f.body.append(f'<rect x="80" y="205" width="1040" height="330" rx="18" fill="none" stroke="{INDIGO}" stroke-width="2" stroke-dasharray="8 7"/>')
    f.text(600, 240, '全体：開発全体の処理量 ── 符号は未決（＋か−かは条件次第）', 16, INDIGO, anchor='middle', weight=700)
    f.box(140, 290, 300, 90, 'AIの生成', '', P, 24); f.box(760, 290, 300, 90, '人間のレビュー', '', TERRA, 24)
    f.text(290, 420, '直接の効能：時間の短縮（＋）', 14, P, anchor='middle', weight=700); f.text(290, 442, '帰属：全体の速さ', 13, MUTED, anchor='middle')
    f.text(910, 420, '直接の効能：欠陥の検出（＋）', 14, TERRA, anchor='middle', weight=700); f.text(910, 442, '帰属：コードという対象', 13, MUTED, anchor='middle')
    f.line(445, 335, 755, 335, color=INK, width=3)
    f.text(600, 320, '関係そのもの', 14, INK, anchor='middle', weight=700)
    f.text(600, 372, '間接の効能：滞留（−）、手戻り（−）', 14, INK, anchor='middle'); f.text(600, 394, '信頼の変化（±）：依存の強度を書き換える', 14, INK, anchor='middle')
    f.text(600, 500, '直接の正と間接の負のどちらが大きいかは、関係の種類からは出てこない', 15, MUTED, anchor='middle')
    f.footer('')
    made.add(f.save('08-c-example-effects.svg'))

    # 9-2 delay and accumulation
    f = rfig(9, '遅延と累積：効能はすぐには見えない', '運動の効果は遅れて現れ、利子は積み上がって閾値を越える', 600, '2')
    for ox, title, c in [(100, '遅延：運動の効果', P), (640, '累積：借金の利子', TERRA)]:
        f.panel(ox - 40, 205, 500, 330, title)
        f.line(ox, 480, ox + 420, 480, color=MUTED, width=2, arrow=True); f.text(ox + 210, 508, '時間 →', 14, MUTED, anchor='middle')
        f.line(ox, 480, ox, 260, color=MUTED, width=2, arrow=True)
    pts = []
    for i in range(41):
        x = 100 + i * 10; n = i / 40
        y = 470 - 170 * (0 if n < 0.45 else min(1, (n - 0.45) / 0.35) ** 1.6)
        pts.append(f'{x:.1f},{y:.1f}')
    f.body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{P}" stroke-width="3"/>')
    f.line(100 + 180, 470, 100 + 180, 300, color=LINE, width=1.5, dash=True); f.text(285, 290, '今日走る', 13, MUTED, anchor='middle'); f.text(430, 290, '効果が現れる', 13, P, anchor='middle', weight=700)
    pts = []
    for i in range(41):
        x = 640 + i * 10; n = i / 40
        y = 470 - 190 * (n ** 2.2)
        pts.append(f'{x:.1f},{y:.1f}')
    f.body.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{TERRA}" stroke-width="3"/>')
    f.line(640, 340, 1060, 340, color=TERRA, width=1.5, dash=True); f.text(1050, 330, '閾値', 13, TERRA, anchor='end', weight=700)
    f.text(850, 300, '越えた瞬間に、全部が一度に現れる', 13, TERRA, anchor='middle')
    f.footer('遅れて現れる効能は、別の原因に帰されやすい。累積する効能は、閾値を越えるまで見えない。')
    made.add(f.save('09-c-delay-accumulation.svg'))

    # 10-2 three substitutes for the missing world
    f = rfig(10, 'ない世界の、三つの代用と、それぞれの穴', '時間で比べる、他と比べる、外してみる', 600, '1')
    cols = [(60, '時間で比べる', '関係を結ぶ前と後', '穴：前と後では、関係以外も変わっている'), (420, '他と比べる', '関係のある組と、ない組', '穴：組が違えば、関係以外も違う'), (780, '外してみる', '関係を一度解消する', '穴：輪の中では戻ってくる。不可逆なら戻らない')]
    for i, (x, title, how, hole) in enumerate(cols):
        f.panel(x, 205, 360, 350, title)
        f.text(x + 180, 275, how, 15, INK, anchor='middle')
        if i == 0:
            f.line(x + 60, 350, x + 300, 350, color=MUTED, width=2, arrow=True); f.text(x + 100, 340, '前', 14, MUTED, anchor='middle'); f.text(x + 260, 340, '後', 14, MUTED, anchor='middle')
            f.blob(x + 100, 400, 40, P, 0.4); f.blob(x + 260, 400, 40, P, 0.6); f.circ(x + 260, 400, 5, TERRA)
        elif i == 1:
            f.blob(x + 100, 370, 36, P, 0.5); f.blob(x + 160, 370, 36, TERRA, 0.5); f.line(x + 110, 370, x + 150, 370, color=INK, width=2)
            f.blob(x + 220, 420, 36, P, 0.5); f.blob(x + 280, 420, 36, TERRA, 0.5)
        else:
            f.blob(x + 110, 390, 44, P, 0.5); f.blob(x + 250, 390, 44, TERRA, 0.5)
            f.line(x + 140, 390, x + 170, 390, color=INK, width=2); f.line(x + 190, 390, x + 220, 390, color=INK, width=2)
            f.line(x + 172, 378, x + 188, 402, color=TERRA, width=2.5); f.line(x + 188, 378, x + 172, 402, color=TERRA, width=2.5)
        f.text(x + 180, 500, hole, 13, TERRA, anchor='middle', weight=700)
    f.footer('代用の穴をどれだけ塞げているかが、価値の主張の確からしさを決める。')
    made.add(f.save('10-b-three-substitutes.svg'))

    # 10-3 three worlds for the example
    f = rfig(10, 'AIの生成 × 人間のレビュー、三つの世界', '今の世界、レビューがない世界、生成がない世界', 650, '3')
    cols = [(60, '今の世界', P, [('生成', P), ('レビュー', TERRA)], '符号は G と R の大小で変わる'), (420, 'レビューがない世界', MUTED, [('生成', P), ('（なし）', LINE)], '速い。欠陥が流出し、手戻りと不可逆の損失が残る'), (780, '生成がない世界', MUTED, [('（人間が書く）', LINE), ('レビュー', TERRA)], '遅い。レビューは追いつき、滞留は起きない')]
    for x, title, c, boxes, note in cols:
        f.panel(x, 205, 360, 370, title)
        for j, (nm, bc) in enumerate(boxes):
            dash = ' stroke-dasharray="7 6"' if bc == LINE else ''
            f.body.append(f'<rect x="{x+40+j*160}" y="290" width="120" height="56" rx="10" fill="#ffffff" stroke="{bc}" stroke-width="2"{dash}/>'); f.text(x + 100 + j * 160, 325, nm, 15, INK if bc != LINE else MUTED, anchor='middle', weight=700)
        f.text(x + 180, 420, note, 13, INK, anchor='middle')
    f.text(420, 520, '差 ＝ レビューの価値', 15, TERRA, anchor='middle', weight=700); f.line(420, 528, 420, 560, color=TERRA, width=1.5)
    f.text(780, 520, '差 ＝ 生成の価値', 15, P, anchor='middle', weight=700); f.line(780, 528, 780, 560, color=P, width=1.5)
    f.footer('ない世界は観測できない。見つかった欠陥から流出したはずの欠陥を見積もる、という推定の穴が残る。')
    made.add(f.save('10-c-three-worlds.svg'))

    # 12-2 cognition loop
    f = rfig(12, '関係を認識すること自体が、知識を生む', '相似を見出す → 抽象化する → 運ぶ → 新しい仮説 → 次の相似', 560, '2')
    nodes = [('相似を見出す', 600, 240), ('共通構造を抽象化する', 930, 360), ('一方の知識を他方へ運ぶ', 600, 480), ('他方に新しい仮説が生まれる', 270, 360)]
    for nm, x, y in nodes:
        f.body.append(f'<rect x="{x-120}" y="{y-24}" width="240" height="48" rx="12" fill="#ffffff" stroke="{P}" stroke-width="2"/>'); f.text(x, y + 6, nm, 15, INK, anchor='middle', weight=700)
    f.path('M 720 250 C 860 270 920 300 930 334', color=P, width=2, arrow=True); f.path('M 925 386 C 900 440 780 470 722 478', color=P, width=2, arrow=True)
    f.path('M 480 478 C 360 470 280 430 272 386', color=P, width=2, arrow=True); f.path('M 272 334 C 290 290 420 255 478 246', color=P, width=2, arrow=True)
    f.text(600, 352, '関係を見た人の側が変わる', 18, INDIGO, anchor='middle', weight=700); f.text(600, 378, '対象について教える以上に', 13, MUTED, anchor='middle')
    f.footer('第1クールで「関係を見出すことがアイデアだ」と言ったことの中身。')
    made.add(f.save('12-b-cognition-loop.svg'))

    # 12-1 example v4
    f = rfig(12, 'AIの生成 × 人間のレビュー（最終形）', '四つの階層と、あいだに置く五つの設計案', 720, 'a')
    running_example(f, 4); f.footer('')
    made.add(f.save('12-a-example-v4.svg'))


# ---------------------------------------------------------------------------
# Part openers: no text, no header, 1200x360, geometric signs only
# ---------------------------------------------------------------------------
def opener(number, title, desc, code='RELEVANCE', accent=INDIGO, subdir=''):
    f = Figure(number, title, desc, 360, '0', code=code, accent=accent, subdir=subdir, header=False)
    # the paper rectangle is drawn by save(); openers have no frame in CSS, so the paper itself is the only ground
    return f


def dial(f, x, y, knob, color):
    f.line(x, y, x + 140, y, color=LINE, width=3)
    for i in range(5):
        f.line(x + i * 35, y - 6, x + i * 35, y + 6, color=LINE, width=1.5)
    f.circ(x + 140 * knob, y, 9, color)


def draw_openers(made: set[str]) -> None:
    # 1-I  point → distribution
    f = opener(1, '第I部 意味は分布である', '点が右へ向かってぼやけた円に変わっていく')
    f.circ(170, 180, 6, INDIGO); f.line(170, 174, 170, 120, color=INDIGO, width=1.5); f.circ(170, 116, 3, INDIGO)
    for i, (x, r, op) in enumerate([(330, 22, 0.9), (500, 48, 0.75), (690, 80, 0.6), (930, 120, 0.5)]):
        f.blob(x, 180, r, INDIGO, op)
    f.line(200, 180, 290, 180, color=LINE, width=1.5, dash=True)
    made.add(f.save('01-0-opener.svg'))

    # 1-II  two distributions, a third rises between them
    f = opener(5, '第II部 関係を見出す', '二つの雲の重なりに、第三の小さな円が立ち上がる')
    f.blob(470, 200, 130, INDIGO); f.blob(730, 200, 130, TEAL)
    f.blob(600, 200, 55, TERRA, 0.7)
    f.circ(600, 70, 8, TERRA); f.path('M 470 110 C 520 80 560 72 592 70', color=TERRA, width=1.5, dash=True); f.path('M 730 110 C 680 80 640 72 608 70', color=TERRA, width=1.5, dash=True)
    made.add(f.save('05-0-opener.svg'))

    # 1-III  a handle floating above a distribution
    f = opener(9, '第III部 言葉という装置', 'ぼやけた円の上に、取っ手の形が一つ浮いている')
    f.blob(600, 230, 115, INDIGO, 0.55)
    f.body.append(f'<rect x="470" y="80" width="260" height="34" rx="17" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    f.line(600, 114, 600, 140, color=TERRA, width=3)
    made.add(f.save('09-0-opener.svg'))

    # 1-IV  the loop
    f = opener(12, '第IV部 結', '四つの点を結ぶ薄い輪')
    pts = [(600, 70), (900, 180), (600, 290), (300, 180)]
    for i, (x, y) in enumerate(pts):
        f.circ(x, y, 10, TERRA if i == 2 else INDIGO)
    f.path('M 612 74 C 760 95 880 140 898 170', color=LINE, width=2, arrow=True); f.path('M 898 190 C 880 230 760 275 612 286', color=LINE, width=2, arrow=True)
    f.path('M 588 286 C 440 275 320 230 302 190', color=LINE, width=2, arrow=True); f.path('M 302 170 C 320 140 440 95 588 74', color=LINE, width=2, arrow=True)
    made.add(f.save('12-0-opener.svg'))

    # 2-I  one thick line unbundles into several
    f = opener(1, '第I部 関係を分ける', '一本の太い線が、右へ向かって色の違う数本の線にほどける', R_CODE, TEAL, R_SUB)
    f.circ(170, 180, 14, TEAL); f.circ(1030, 180, 14, TEAL)
    f.line(184, 180, 560, 180, color=INK, width=9)
    for dy, c in [(-66, TEAL), (-22, TERRA), (22, MUTED), (66, INDIGO)]:
        f.path(f'M 560 180 C 700 180 760 {180+dy} 880 {180+dy} L 1016 {180+dy*0.35:.0f}', color=c, width=3)
    made.add(f.save('01-0-opener.svg'))

    # 2-II  four tiles: compare, function, time, meaning
    f = opener(4, '第II部 関係の種類をめぐる', '比べる・役割・時間・意味の四つの小さなタイル', R_CODE, TEAL, R_SUB)
    xs = [210, 470, 730, 990]
    for x in xs:
        f.body.append(f'<rect x="{x-105}" y="60" width="210" height="240" rx="18" fill="none" stroke="{LINE}" stroke-width="2"/>')
    f.circ(xs[0] - 38, 180, 30, TEAL, fill=False, width=3); f.circ(xs[0] + 38, 180, 30, TEAL, fill=False, width=3); f.line(xs[0], 100, xs[0], 260, color=LINE, width=1.5, dash=True)
    f.body.append(f'<rect x="{xs[1]-75}" y="110" width="150" height="140" rx="12" fill="none" stroke="{LINE}" stroke-width="2" stroke-dasharray="7 6"/>')
    f.body.append(f'<rect x="{xs[1]-55}" y="150" width="44" height="44" rx="8" fill="#ffffff" stroke="{TEAL}" stroke-width="3"/><rect x="{xs[1]+11}" y="150" width="44" height="44" rx="8" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    f.path(f'M {xs[2]+48} 150 A 50 50 0 1 1 {xs[2]+20} 134', color=TEAL, width=3, arrow=True)
    f.blob(xs[3] - 25, 180, 60, TEAL); f.blob(xs[3] + 25, 180, 60, TERRA)
    made.add(f.save('04-0-opener.svg'))

    # 2-III  something grows between two boxes
    f = opener(8, '第III部 関係は何を生むか', '二つの箱の間から上へ伸びる線と、プラスとマイナスの印', R_CODE, TEAL, R_SUB)
    f.body.append(f'<rect x="200" y="150" width="220" height="80" rx="14" fill="#ffffff" stroke="{TEAL}" stroke-width="3"/><rect x="780" y="150" width="220" height="80" rx="14" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    f.line(420, 190, 780, 190, color=LINE, width=2)
    f.path('M 600 190 C 600 150 590 110 600 70', color=TEAL, width=3); f.path('M 600 150 C 575 140 560 125 556 110', color=TEAL, width=2.5); f.path('M 600 110 C 625 100 640 85 644 72', color=TEAL, width=2.5)
    f.line(515, 262, 545, 262, color=TEAL, width=4); f.line(530, 247, 530, 277, color=TEAL, width=4)
    f.line(655, 262, 685, 262, color=TERRA, width=4)
    made.add(f.save('08-0-opener.svg'))

    # 2-IV  the boxes stay; the space between gets dials
    f = opener(11, '第IV部 関係を設計する', '二つの箱は同じまま。あいだに、つまみが三つ並ぶ', R_CODE, TEAL, R_SUB)
    f.body.append(f'<rect x="150" y="150" width="220" height="80" rx="14" fill="#ffffff" stroke="{TEAL}" stroke-width="3"/><rect x="830" y="150" width="220" height="80" rx="14" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    dial(f, 530, 110, 0.3, TEAL); dial(f, 530, 190, 0.7, TERRA); dial(f, 530, 270, 0.5, INK)
    made.add(f.save('11-0-opener.svg'))


if __name__ == '__main__':
    main()
