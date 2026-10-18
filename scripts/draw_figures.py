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
    def __init__(self, number: int, title: str, subtitle: str, height: int = 680, part: str = ''):
        self.h = height
        self.n = number
        self.part = part
        self.defs: list[str] = ['<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="#5d6873" stroke-width="1.4"/></marker>']
        self.body: list[str] = []
        self.title = title
        self.subtitle = subtitle
        self.gradients = 0
        label = 'RELEVANCE' if number == 0 else f'RELEVANCE     {number:02d}' + (f'     図{number}-{part}' if part else '')
        self.text(50, 52, label, 18, INDIGO, weight=700)
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
        gid = f'g{self.n:02d}{self.part}-{self.gradients}'
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
        OUT.mkdir(parents=True, exist_ok=True)
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.h}" viewBox="0 0 1200 {self.h}" role="img" aria-labelledby="title desc">',
                f'<title id="title">{escape(self.title)}</title>', f'<desc id="desc">{escape(self.subtitle)}</desc>',
                '<defs>' + ''.join(self.defs) + '</defs>', f'<rect width="1200" height="{self.h}" rx="20" fill="{BG}"/>',
                f'<g font-family=\'{FONT}\'>']
        (OUT / name).write_text('\n'.join(head + self.body + ['</g>', '</svg>']) + '\n', encoding='utf-8')
        return name


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


def main() -> None:
    series = json.loads((ROOT / 'series.json').read_text(encoding='utf-8'))
    expected = {Path(p).name for c in series['chapters'] for p in c['figures']} | {'00-cover.svg'}
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

    missing, extra = expected - made, made - expected
    if missing or extra:
        raise SystemExit(f'series.json mismatch. missing={sorted(missing)} extra={sorted(extra)}')
    for stale in OUT.glob('*.svg'):
        if stale.name not in made:
            stale.unlink()
    print(f'Generated {len(made)} SVG files in {OUT}')


if __name__ == '__main__':
    main()
