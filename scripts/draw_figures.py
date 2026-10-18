#!/usr/bin/env python3
"""Generate the 13 original SVG illustrations (cover + 12 chapters) deterministically. Stdlib only."""
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
    def __init__(self, number: int, title: str, subtitle: str, height: int = 680):
        self.h = height
        self.n = number
        self.defs: list[str] = ['<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="#5d6873" stroke-width="1.4"/></marker>']
        self.body: list[str] = []
        self.title = title
        self.subtitle = subtitle
        self.gradients = 0
        label = 'RELEVANCE' if number == 0 else f'RELEVANCE     {number:02d}'
        self.text(50, 52, label, 18, INDIGO, weight=700)
        self.text(50, 103, title, 34, weight=700)
        self.text(50, 141, subtitle, 21, MUTED)
        self.line(50, 166, 1150, 166, color=LINE, width=1)

    # primitives
    def text(self, x, y, s, size=24, color=INK, anchor='start', weight=400, italic=False):
        style = ' font-style="italic"' if italic else ''
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}"{style}>{escape(str(s))}</text>')

    def line(self, x1, y1, x2, y2, color=MUTED, width=2, arrow=False, dash=False, start_arrow=False):
        extra = (' marker-end="url(#arrow)"' if arrow else '') + (' marker-start="url(#arrow)"' if start_arrow else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.body.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def path(self, d, color=MUTED, width=2, arrow=False, dash=False, fill='none'):
        extra = (' marker-end="url(#arrow)"' if arrow else '') + (' stroke-dasharray="8 7"' if dash else '')
        self.body.append(f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}"{extra}/>')

    def box(self, x, y, w, h, title, subtitle='', color=INDIGO, size=24):
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="{color}" stroke-width="2"/>')
        self.text(x + w / 2, y + (h / 2 + 8 if not subtitle else h / 2 - 4), title, size, color, anchor='middle', weight=700)
        if subtitle:
            self.text(x + w / 2, y + h / 2 + 28, subtitle, 19, MUTED, anchor='middle')

    def circ(self, x, y, r=10, color=INDIGO, fill=True, dash=False):
        if fill:
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>')
        else:
            extra = ' stroke-dasharray="7 6"' if dash else ''
            self.body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="{color}" stroke-width="2"{extra}/>')

    def panel(self, x, y, w, h, label=''):
        self.body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#c9c4b6" stroke-width="2" stroke-dasharray="7 7"/>')
        if label:
            self.text(x + w / 2, y + 34, label, 23, INK, anchor='middle', weight=700)

    def blob(self, cx, cy, r, color, opacity=0.55):
        """A soft-edged disc: the visual sign of a distribution without a boundary."""
        self.gradients += 1
        gid = f'g{self.n:02d}-{self.gradients}'
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

    def gy(self, x, cx, base, height, sigma):
        return base - height * math.exp(-((x - cx) ** 2) / (2 * sigma ** 2))

    def footer(self, s):
        self.text(50, self.h - 28, s, 19, MUTED)

    def save(self, name: str):
        OUT.mkdir(parents=True, exist_ok=True)
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{self.h}" viewBox="0 0 1200 {self.h}" role="img" aria-labelledby="title desc">',
                f'<title id="title">{escape(self.title)}</title>', f'<desc id="desc">{escape(self.subtitle)}</desc>',
                '<defs>' + ''.join(self.defs) + '</defs>', f'<rect width="1200" height="{self.h}" rx="20" fill="{BG}"/>',
                f'<g font-family=\'{FONT}\'>']
        (OUT / name).write_text('\n'.join(head + self.body + ['</g>', '</svg>']) + '\n', encoding='utf-8')


def spread(cx, cy, r, n, seed):
    """Deterministic quasi-uniform points in a disc (golden-angle spiral)."""
    pts = []
    for i in range(n):
        t = (i + seed) * 2.399963
        rr = r * math.sqrt((i + 0.5) / n)
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts


def main() -> None:
    chapters = json.loads((ROOT / 'series.json').read_text(encoding='utf-8'))['chapters']
    fn = {c['number']: Path(c['figure']).name for c in chapters}

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
    f.save('00-cover.svg')

    # 01 reverse engineering
    f = Figure(1, '仕組みを知るのではなく、振る舞いを逆再生する', 'LLMの「分かっているように見える」を手がかりに、意味とは何かへ戻る')
    f.box(80, 230, 330, 150, 'LLM', '確率的に尤もらしい次の語を選ぶ', INDIGO, 30)
    for i, (w, p) in enumerate([('鳥が', 0.9), ('飛ぶ', 0.72), ('泳ぐ', 0.18), ('鳴く', 0.44)]):
        y = 240 + i * 34
        f.text(455, y + 22, w, 19, INK)
        f.body.append(f'<rect x="520" y="{y+6}" width="{int(140*p)}" height="18" rx="4" fill="{INDIGO}" opacity="{0.35+0.5*p:.2f}"/>')
    f.text(590, 395, '次の語の確率', 17, MUTED, anchor='middle')
    f.box(790, 230, 330, 150, '意味とはなにか', '人間の側で起きていること', TEAL, 30)
    f.line(700, 305, 785, 305, color=TEAL, width=3, arrow=True)
    f.text(742, 285, '見えるもの', 16, MUTED, anchor='middle')
    f.line(785, 345, 700, 345, color=TERRA, width=3, arrow=True)
    f.text(742, 372, '逆再生', 18, TERRA, anchor='middle', weight=700)
    f.panel(80, 450, 1040, 150)
    f.box(130, 485, 300, 80, '蒸気機関', '先に動いていた', MUTED, 22)
    f.line(435, 525, 545, 525, arrow=True)
    f.text(490, 512, '後から', 16, MUTED, anchor='middle')
    f.box(550, 485, 300, 80, '熱力学', '原理が追いついた', MUTED, 22)
    f.text(1000, 520, '先行するモデルが', 21, INK, anchor='middle', weight=700)
    f.text(1000, 550, '本質を暗示する', 21, INK, anchor='middle', weight=700)
    f.footer('知りたいのはLLMの仕組みではなく、その振る舞いから照らし返される「意味」の正体。')
    f.save(fn[1])

    # 02 similarity is not a line
    f = Figure(2, '「似ている」は、二点を結ぶ一本の線ではない', '判定は見る側の前提で割れ、前提を揃えても境目は引けない')
    f.panel(60, 205, 330, 400, '頭の中のイメージ')
    f.circ(130, 400, 13, INDIGO); f.circ(320, 400, 13, TEAL)
    f.line(143, 400, 307, 400, color=INK, width=3)
    f.text(130, 445, 'A', 22, INDIGO, anchor='middle', weight=700); f.text(320, 445, 'B', 22, TEAL, anchor='middle', weight=700)
    f.text(225, 380, '線がある？', 19, MUTED, anchor='middle')
    f.text(225, 560, '線は、AとBの間にはなく', 18, INK, anchor='middle')
    f.text(225, 586, '見る側の前提の中にある', 18, INK, anchor='middle')
    f.panel(430, 205, 330, 400, '不揃いな前提')
    f.text(595, 265, 'トマト と リンゴ', 21, INK, anchor='middle', weight=700)
    f.box(470, 300, 250, 62, '台所：違う', '野菜と果物', TERRA, 20)
    f.box(470, 385, 250, 62, '植物学：同じ', 'どちらも果実', TEAL, 20)
    f.box(470, 470, 250, 62, '食卓：似ている', '赤くて丸い', INDIGO, 20)
    f.text(595, 575, 'どれも正しい。前提が違うだけ', 17, MUTED, anchor='middle')
    f.panel(800, 205, 340, 400, '境界は明確か？')
    f.gradients += 1
    f.defs.append('<linearGradient id="g02-bar" x1="0" x2="1"><stop offset="0" stop-color="#2b5fd9"/><stop offset="1" stop-color="#2fa36a"/></linearGradient>')
    f.body.append('<rect x="840" y="300" width="260" height="56" rx="10" fill="url(#g02-bar)"/>')
    f.text(840, 385, '青', 20, '#2b5fd9', weight=700); f.text(1100, 385, '緑', 20, '#2fa36a', anchor='end', weight=700)
    for x in (900, 950, 1000, 1050):
        f.line(x, 300, x, 356, color='#ffffff', width=1, dash=True)
        f.text(x, 290, '？', 16, MUTED, anchor='middle')
    f.text(970, 440, 'どこから緑？', 20, INK, anchor='middle', weight=700)
    f.text(970, 500, '言葉には輪郭があるが', 18, INK, anchor='middle')
    f.text(970, 526, '言葉が指すものには輪郭がない', 18, INK, anchor='middle')
    f.text(970, 575, '白黒ではなく、濃淡', 17, MUTED, anchor='middle')
    f.footer('食い違いの根は、意味に明確な境界があるという無意識の前提にある。')
    f.save(fn[2])

    # 03 distribution
    f = Figure(3, '意味は、ぼやけた縁を持つぼやけた丸', '砂の山：頂上が典型例、裾はどこまでも薄く続き、ゼロにならない')
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
    f.panel(60, 215, 300, 200)
    f.gauss(140, 395, 140, 18, 80, 200, TEAL, 2.5); f.text(140, 240, '尖った山', 16, TEAL, anchor='middle', weight=700); f.text(140, 262, '正三角形', 15, MUTED, anchor='middle')
    f.gauss(280, 395, 55, 48, 205, 355, TERRA, 2.5); f.text(280, 240, '平たい山', 16, TERRA, anchor='middle', weight=700); f.text(280, 262, '道具・もの', 15, MUTED, anchor='middle')
    f.footer('白か黒かは決められないが、どれくらい灰色かは決められる。')
    f.save(fn[3])

    # 04 anisotropy
    f = Figure(4, '空間そのものが、ある方向に歪んで圧縮されている', '等方的な散らばり（素朴な絵）と、狭い円錐に密集する異方性（実測）')
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
    f.save(fn[4])

    # 05 relation as distribution
    f = Figure(5, '関係もまた分布。だから「間」と「中」は両立する', '二つの雲の重なりに立ち上がる意味と、どの範囲を一塊と見るかの切り替え', 700)
    f.blob(250, 380, 150, TEAL); f.blob(420, 380, 150, TERRA)
    f.text(190, 385, '海', 30, TEAL, anchor='middle', weight=700); f.text(480, 385, '夏', 30, TERRA, anchor='middle', weight=700)
    f.text(335, 352, '海水浴', 17, INK, anchor='middle', weight=700); f.text(335, 376, '日焼け・花火', 15, INK, anchor='middle'); f.text(335, 398, '潮の匂い', 15, INK, anchor='middle'); f.text(335, 420, '…', 15, MUTED, anchor='middle')
    f.text(335, 560, '関係は意味であり、意味は分布', 19, INK, anchor='middle', weight=700)
    f.text(335, 588, 'ゆえに関係も分布', 19, INK, anchor='middle')
    f.panel(640, 215, 490, 230, '')
    f.text(885, 250, '関西', 22, MUTED, anchor='middle', weight=700)
    f.circ(730, 350, 12, INDIGO); f.circ(1040, 350, 12, INDIGO)
    f.text(730, 392, '大阪', 19, INK, anchor='middle'); f.text(1040, 392, '京都', 19, INK, anchor='middle')
    f.line(745, 350, 1025, 350, color=INDIGO, width=2, dash=True)
    for x, nm in [(830, '高槻'), (885, '淀川'), (940, '山崎')]:
        f.circ(x, 350, 6, TERRA); f.text(x, 330, nm, 14, TERRA, anchor='middle')
    f.text(885, 425, '大阪と京都の「間にある」 ＝ 関西の「中にある」', 17, INK, anchor='middle')
    f.panel(640, 470, 490, 190, '')
    tx, ty = 760, 565
    for r in (28, 56, 84):
        f.circ(tx, ty, r, LINE, fill=False)
    f.circ(tx, ty, 6, INDIGO)
    for k in range(4):
        a1 = -0.6 + k * 0.4
        p1 = (tx + 28 * math.cos(a1), ty + 28 * math.sin(a1)); f.line(tx, ty, *p1, color=INDIGO, width=1.5); f.circ(*p1, 4, INDIGO)
        for j in (-0.18, 0.18):
            p2 = (tx + 56 * math.cos(a1 + j), ty + 56 * math.sin(a1 + j)); f.line(*p1, *p2, color=TEAL, width=1.2); f.circ(*p2, 3, TEAL)
            for m in (-0.08, 0.08):
                p3 = (tx + 84 * math.cos(a1 + j + m), ty + 84 * math.sin(a1 + j + m)); f.line(*p2, *p3, color=TERRA, width=1); f.circ(*p3, 2.5, TERRA)
    f.text(960, 540, '双曲空間：外へ向かうほど', 17, INK, anchor='middle', weight=700)
    f.text(960, 566, '場所が指数的に増え、枝がぶつからない', 15, MUTED, anchor='middle')
    f.text(960, 600, '中心＝抽象、縁＝具体', 15, MUTED, anchor='middle')
    f.text(960, 626, '近いこと と 包含されること が同時に成り立つ', 14, MUTED, anchor='middle')
    f.footer('家族的類似：同じ枝の中にいながら、典型例からの距離が違う。')
    f.save(fn[5])

    # 06 ideas as finding relations
    f = Figure(6, 'アイデアとは関係を見出すこと。見出された関係は仮説', '「関係なさそう」に隠れた時間の指標と、検証による二つの行き先', 700)
    f.blob(260, 300, 95, INDIGO); f.blob(560, 300, 95, TEAL)
    f.text(260, 305, 'A', 30, INDIGO, anchor='middle', weight=700); f.text(560, 305, 'B', 30, TEAL, anchor='middle', weight=700)
    f.text(410, 312, '？', 42, TERRA, anchor='middle', weight=700)
    f.text(410, 365, '間には何がありますか', 17, MUTED, anchor='middle')
    f.text(880, 240, '「関係なさそう」の三つの段階', 20, INK, anchor='middle', weight=700)
    for i, s in enumerate(['一見、関係なさそう', '「現時点では」関係なさそう', 'まだ関係を発見できていない', 'これから関係していく']):
        y = 270 + i * 40
        f.circ(735, y + 6, 6, TERRA if i < 3 else TEAL)
        f.text(755, y + 12, s, 18, INK)
        if i < 3:
            f.line(735, y + 14, 735, y + 38, color=LINE, width=2)
    f.text(600, 445, '関連は仮説に過ぎない', 28, INDIGO, anchor='middle', weight=700)
    f.line(600, 462, 600, 500, color=MUTED, width=2, arrow=True)
    f.text(640, 490, '行動による検証', 17, MUTED)
    f.box(120, 520, 430, 110, '検証された', 'ゴボウの実 → 面ファスナー：何年もの試作を経て', TEAL, 24)
    f.body.append(f'<rect x="650" y="520" width="430" height="110" rx="14" fill="#ffffff" stroke="{TERRA}" stroke-width="2" stroke-dasharray="8 7"/>')
    f.text(865, 571, '検証で消えた', 24, TERRA, anchor='middle', weight=700)
    f.text(865, 603, '血液型 → 性格：信じられ、行動されたが、支持されず', 19, MUTED, anchor='middle')
    f.footer('見出すことと検証することは、別の行為。既存の要素の新しい組み合わせ（ヤング）。')
    f.save(fn[6])

    # 07 two hop
    f = Figure(7, '直接つながっていなくても、共通の媒介を介して結ばれる', '2ホップリンクと、媒介が重なるほど太くなる関係')
    f.circ(130, 400, 16, INDIGO); f.text(130, 445, '和歌山', 20, INK, anchor='middle', weight=700)
    f.circ(530, 400, 16, INDIGO); f.text(530, 445, '愛媛', 20, INK, anchor='middle', weight=700)
    f.circ(330, 270, 18, TERRA); f.text(330, 245, 'みかん', 20, TERRA, anchor='middle', weight=700)
    f.line(145, 392, 313, 280, color=TERRA, width=3); f.line(515, 392, 347, 280, color=TERRA, width=3)
    for y, nm, c in [(340, '温暖な気候', TEAL), (470, '海に面している', TEAL), (540, '巡礼の文化', TEAL)]:
        f.circ(330, y, 7, c); f.text(330, y - 14 if y < 400 else y + 26, nm, 14, c, anchor='middle')
        f.line(144, 400, 324, y, color=c, width=1.2); f.line(516, 400, 336, y, color=c, width=1.2)
    f.line(150, 400, 510, 400, color=INDIGO, width=2, dash=True)
    f.text(330, 418, '直接の線はない。それでも意味がある', 14, MUTED, anchor='middle')
    f.text(330, 600, '媒介が重なるほど、関係は太くなる', 19, INK, anchor='middle', weight=700)
    f.panel(660, 205, 480, 400, '周囲が中心を浮かび上がらせる')
    f.circ(900, 420, 48, INDIGO, fill=False, dash=True); f.text(900, 428, 'X', 30, INDIGO, anchor='middle', weight=700)
    f.text(900, 486, '名前が出てこない', 14, MUTED, anchor='middle')
    for ang, nm in [(-2.3, '刑事ドラマ'), (-0.8, 'あの女優と共演'), (0.6, '関西の出身'), (2.4, '昔はお笑い')]:
        x, y = 900 + 150 * math.cos(ang), 420 + 130 * math.sin(ang)
        f.circ(x, y, 8, TERRA)
        ex, ey = 900 + 58 * math.cos(ang), 420 + 58 * math.sin(ang)
        f.line(x, y, ex, ey, color=TERRA, width=1.5, arrow=True)
        f.text(x, y + (-16 if math.sin(ang) < 0 else 28), nm, 15, INK, anchor='middle')
    f.footer('PageRankの変種やGraphRAGとして、すでに実装されている回路。人間の連想も同じ形。')
    f.save(fn[7])

    # 08 generation cheap, evaluation expensive
    f = Figure(8, '生成は安く、評価は高い', '組み合わせは爆発するが、価値あるものは指数的に少ない')
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
    f.panel(80, 500, 1040, 110)
    for i, (n, pct, c) in enumerate([('1 作品から', '100% → パクリ', TERRA), ('100 作品から 1% ずつ', 'ほぼオリジナル', INDIGO), ('10000 作品から 0.01% ずつ', '元が分からなくなる', TEAL)]):
        x = 110 + i * 345
        f.text(x, 545, n, 18, c, weight=700); f.text(x, 575, pct, 16, MUTED)
    f.text(600, 650, '差は、盗んだ量ではなく、評価した量', 20, INK, anchor='middle', weight=700)
    f.footer('')
    f.save(fn[8])

    # 09 A, B or C
    f = Figure(9, 'A か B か、ではなく「A、B or C」', 'せめぎ合いの間隙からふいに現れる第三のものが、AとBの関係を読み替える')
    f.blob(330, 440, 150, INDIGO); f.blob(560, 440, 150, TEAL)
    f.text(265, 445, '紙', 32, INDIGO, anchor='middle', weight=700); f.text(625, 445, '画面', 32, TEAL, anchor='middle', weight=700)
    f.text(265, 480, '目に優しい・手触り', 14, MUTED, anchor='middle'); f.text(625, 480, '何千冊・検索', 14, MUTED, anchor='middle')
    f.line(380, 440, 420, 440, color=INDIGO, width=3, arrow=True); f.line(510, 440, 470, 440, color=TEAL, width=3, arrow=True)
    f.path('M 445 400 L 445 300', color=TERRA, width=3, arrow=True)
    f.body.append(f'<polygon points="445,215 455,250 492,255 462,278 470,315 445,297 420,315 428,278 398,255 435,250" fill="{TERRA}" opacity="0.9"/>')
    f.text(445, 190, 'or C：電子ペーパー', 22, TERRA, anchor='middle', weight=700)
    f.text(445, 585, '紙であり、画面である。矛盾がそのまま魅力になる', 18, INK, anchor='middle', weight=700)
    f.text(445, 612, '間隙は一瞬しか開かない。取り出しが遅いとCは消える', 15, MUTED, anchor='middle')
    f.panel(760, 205, 380, 410, '比喩：二つの分布を重ねる')
    f.blob(900, 390, 90, INDIGO); f.blob(1000, 390, 90, TERRA)
    f.text(860, 395, '市場', 22, INDIGO, anchor='middle', weight=700); f.text(1045, 395, '熊', 22, TERRA, anchor='middle', weight=700)
    f.text(950, 480, '「市場は熊だ」', 20, INK, anchor='middle', weight=700)
    f.text(950, 510, '重ねた瞬間、間に何かが立ち上がる', 15, MUTED, anchor='middle')
    f.text(950, 560, '直喩は距離を残し、隠喩はゼロにし、', 14, MUTED, anchor='middle')
    f.text(950, 582, '擬人法は人間という分布を重ねる', 14, MUTED, anchor='middle')
    f.footer('比喩は、言葉から言葉をつくる二次創作であり、新しいものに最初の名前を与える行為でもある。')
    f.save(fn[9])

    # 10 hallucination and creation
    f = Figure(10, '生成の中に、事実と虚構を分けるものはない', '同じ一文、同じ機構。差は後段の検証レイヤーの有無だけ', 700)
    f.box(70, 300, 300, 100, '生成', '確率的に次の語を選ぶ', INDIGO, 24)
    f.line(375, 350, 440, 350, color=MUTED, width=2, arrow=True)
    f.body.append(f'<rect x="445" y="305" width="330" height="90" rx="12" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>')
    f.text(610, 342, '「1890年、ロンドンに', 19, INK, anchor='middle'); f.text(610, 370, '一人の探偵が住んでいた」', 19, INK, anchor='middle')
    f.path('M 775 330 C 820 330 820 250 860 250', color=TERRA, width=2, arrow=True)
    f.path('M 775 370 C 820 370 820 520 860 520', color=TEAL, width=2, arrow=True)
    f.box(865, 205, 265, 90, '検証レイヤー', '外部の事実と照合', TERRA, 21)
    f.line(997, 300, 997, 325, color=MUTED, width=1.5)
    f.line(997, 325, 930, 345, color=MUTED, width=1.5, arrow=True); f.line(997, 325, 1064, 345, color=MUTED, width=1.5, arrow=True)
    f.text(915, 380, '一致', 16, TEAL, anchor='middle', weight=700); f.text(915, 404, '事実', 19, INK, anchor='middle', weight=700)
    f.text(1080, 380, '不一致', 16, TERRA, anchor='middle', weight=700); f.text(1080, 404, 'ハルシネーション', 19, INK, anchor='middle', weight=700)
    f.body.append(f'<rect x="865" y="475" width="265" height="90" rx="12" fill="none" stroke="{TEAL}" stroke-width="2" stroke-dasharray="8 7"/>')
    f.text(997, 512, '検証なし', 21, TEAL, anchor='middle', weight=700); f.text(997, 542, '→ 創作として読まれる', 17, MUTED, anchor='middle')
    f.text(610, 450, '文は一字も変わっていない。変わったのは外側だけ', 17, MUTED, anchor='middle')
    f.panel(70, 490, 705, 140)
    f.text(422, 530, '記憶も同じ形をしている', 20, INK, anchor='middle', weight=700)
    f.text(422, 565, '思い出すこと ＝ 生成。本当にあったかは、記録や他人の証言と照合して初めて確定する', 15, MUTED, anchor='middle')
    f.text(422, 595, '関連も、記憶も、出力も、生成された時点ではすべて仮説', 16, INDIGO, anchor='middle', weight=700)
    f.footer('評価（価値があるか）と検証（現実と一致するか）は、基準が違うだけで同じ位置にある同じ行為。')
    f.save(fn[10])

    # 11 words as handles
    f = Figure(11, '言葉は、意味を掴んで動かすための取っ手', '人間は取っ手の先に体験という鍋を持つ。LLMは取っ手だけを直接扱う', 700)
    f.panel(60, 205, 520, 420, '人間：鍋に取っ手がついている')
    f.blob(300, 450, 125, INDIGO, 0.5)
    f.text(300, 445, '意味', 26, INDIGO, anchor='middle', weight=700); f.text(300, 472, 'ぼやけた分布', 15, MUTED, anchor='middle')
    f.body.append(f'<rect x="150" y="300" width="300" height="34" rx="17" fill="#ffffff" stroke="{TERRA}" stroke-width="3"/>')
    f.text(300, 324, '言葉（取っ手）', 19, TERRA, anchor='middle', weight=700)
    f.line(300, 334, 300, 345, color=TERRA, width=3)
    f.text(300, 590, '体験 → 違和感 → 周囲に断片 → 仮の名前', 15, MUTED, anchor='middle')
    f.text(300, 614, '切れたら、体験まで降りて結び直せる', 15, MUTED, anchor='middle')
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
    f.save(fn[11])

    # 12 conclusion loop
    f = Figure(12, '関連は仮説であり、評価がそれを検証する', '見出す → 言葉に固定する → 検証する → 世界の側に置かれる、という循環', 720)
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
    f.save(fn[12])
    print(f'Generated {len(chapters) + 1} SVG files in {OUT}')


if __name__ == '__main__':
    main()
