# ビューア可読性の改善計画

作成日: 2026-10-21
参考: https://yamaguchiyoshito.github.io/sier-resource-series/ （リポジトリ yamaguchiyoshito/sier-resource-series、2026-10-21 時点で9コミット）
状態: 計画。本リポジトリの CSS・ビルドは変更していない。

---

## 1. 参考リポジトリの対応履歴と、その意図

参考リポジトリは本リポジトリと同じ骨格（Pandoc → HTML、CSSのみの目次ドロワー、SVG挿絵）から出発し、初回コミットのあと7回の可読性改善を重ねている。順に追うと、意図は「本文の行長と行間を読み物向けに整える → 図と表を本文幅に収める → 表の見え方を細かく直す → 出典をクリックできるようにする」という一方向の流れになっている。

| 順 | コミット | 変更内容 | 意図（コミット本文から） |
| --- | --- | --- | --- |
| 1 | `170b4da` Improve reader typography and figure sizing | CSSを全面改稿。本文カラム幅 720px、本文 16px／行間 1.75／字間 .012em、見出しを h2 下線・h3 18px の階層に、図版を 660px 上限の白枠つきで中央表示、表に縞模様と軽い罫線、ヘッダーを固定（半透明＋ぼかし）、記事冒頭の前後ナビ（blockquote）をカード状に、`em` を斜体でなく灰色の正体に、リストの余白を詰める、ダークモードと狭い画面の調整 | 「Claude Desktop の Markdown ビューアを参考に、読みやすさ（本文の行長・行間・見出し階層）と図版の適正サイズを優先する」 |
| 2 | `40e54fa` Keep header actions on one line at phone width | ブランドを `flex:1 1 auto; min-width:0`、操作部を `nowrap`、600px 以下でブランドの小見出し（eyebrow）を非表示 | 電話幅でヘッダーの「読み方／目次」が折り返していた |
| 3 | `b87f27c` Wrap tables in a scroll container | `build.py` で `<table>` を `div.table-wrap` で包み、枠・角丸・横スクロールをラッパー側へ | `table` を `display:block` にしていたため、角丸の外枠だけが全幅に伸びて行が内容幅で止まっていた |
| 4 | `8274ba0` Left-align display math | ブロック数式を左寄せ＋1.5em インデント、背景なし | 短い定義式が全幅の背景ボックスの左端に浮いて見えていた（本リポジトリは数式を使わないので対象外） |
| 5 | `e5c47ab` Let browsers size table columns by content | Pandoc に `--columns=10000` を渡し、パイプテーブルの区切り行由来の相対列幅（colgroup）を付けさせない | 番号列などの短い列が本文列と同じ幅になっていた |
| 6 | `b50bb29` Shrink tables to content width | `.table-wrap{width:fit-content;max-width:100%}`、`table{width:auto}` | 短い表まで本文幅に引き伸ばされていた |
| 7 | `318588c` Autolink bare URLs | Pandoc の `autolink_bare_uris` を有効化。`::` を含む DOI は `<URL>` 記法に | 参考文献の素のURLがクリックできなかった |

このほか初回コミットの時点で、本リポジトリにない仕組みが二つある。

- 目次ドロワーを「部」（`series.json` の `cours`）で区切って見出しを入れる（`.toc-cour`、`.toc-part`）。
- トップページの `<title>` を連載名だけにし、章ページは「章名 | 連載名」にする。

## 2. 本リポジトリの現状（2026-10-21、ローカルビルドと電話幅の実表示で確認）

| 項目 | 本リポジトリ | 参考 |
| --- | --- | --- |
| 本文カラム幅 | 860px | 720px |
| 本文 | 17px／行間 1.95 | 16px／行間 1.75／字間 .012em |
| 見出し | h3 を左縦棒で強調、h2 は副題専用 | h2 下線、h3 18px 太字。副題は h1+h2 |
| 前後ナビ | 本文中の素の段落（← 第4回 \| 連載目次 \| 第6回 →） | 冒頭 blockquote をカード状に |
| ヘッダー | 固定しない。ブランド 24px＋小見出し | 固定（半透明＋ぼかし）。ブランド 17px、電話幅では小見出し非表示 |
| 図版 | 本文幅いっぱい（860px）、枠なし | 660px 上限、白枠・角丸・余白つきで中央 |
| 図のキャプション | **二重表示**：Pandoc の implicit_figures が alt を `<figcaption>` として出し、その直後に本文の `*図N-k：…*` 段落が続く。1章あたり図の数だけ重複（第2クール第5回で3組） | alt だけをキャプションに使う（`figcaption` と `p:has(>em:only-child)` を同じ見た目に） |
| 斜体 | キャプションが日本語の斜体で表示される | `em{font-style:normal;color:var(--muted)}` |
| 電話幅の図 | 1200px 幅の SVG が 343px に縮小され、図中の 13〜17px の文字が 4〜5px 相当になって読めない | SVG は 1000px 基準で文字が大きめ。それでも縮小はされる |
| 表 | `table{display:block}`（参考が問題視した状態）。トップの目次表、設計書、校正記録、編集ガイドに表がある | `div.table-wrap` ＋ `fit-content` ＋ `--columns=10000` |
| ページタイトル | トップが「意味の関連性 \| 意味の関連性」と重複 | 連載名のみ |
| 目次ドロワー | 12回を平坦に並べる。別の連載へのリンクあり | 部ごとに見出し |
| ダークモード | 図の背景を紙色に固定 | 同じ＋図に枠線 |
| 参考文献のURL | 明示リンクのみなので問題なし | 自動リンク |

参考がコミットごとに潰した問題のうち、表の三件とヘッダー折り返しは、本リポジトリにもそのまま存在する。それに加えて、本リポジトリ固有の問題が二つある。図のキャプション二重表示と、電話幅で図の文字が読めないこと。

## 3. 改善計画

優先度は、読者に見えている不具合 → 参考が実証した可読性の底上げ → 構造の整備、の順。

### 段階A　不具合の修正（最優先、小さい変更）

| # | 内容 | 変更場所 | 根拠 |
| --- | --- | --- | --- |
| A1 | 図のキャプション二重表示をなくす。`build.py` で、画像の直後にある `*図N-k：…*` 段落を `<figcaption>` に取り込み、alt は `alt` 属性に留める（Pandoc の `implicit_figures` を外すか、生成後に `<figure>` を組み直す）。検査 `check_html.py` に「図の数とキャプションの数が一致し、`figcaption` が二重でない」を追加 | `scripts/build.py`、`scripts/check_html.py` | 現状、全50図で重複している |
| A2 | トップページの `<title>` を連載名のみに。章ページは「章名 \| 連載名」のまま | `scripts/build.py` | 参考の初回実装 |
| A3 | 表を `div.table-wrap` で包み、`fit-content`＋横スクロール、`--columns=10000`。`table{display:block}` をやめる | `scripts/build.py`、`site-src/styles.css` | 参考 `b87f27c`・`e5c47ab`・`b50bb29` |
| A4 | 電話幅でヘッダーを一行に（ブランド縮小、小見出し非表示、操作部 nowrap） | `site-src/styles.css` | 参考 `40e54fa` |

### 段階B　読み物としての底上げ（参考 `170b4da` の移植）

| # | 内容 | 変更場所 | 補足 |
| --- | --- | --- | --- |
| B1 | 本文カラム 720px、本文 16px／行間 1.75〜1.8／字間 .012em。`-webkit-text-size-adjust`、`text-rendering` も揃える | `styles.css` | 日本語の長文では 1行 45字前後が読みやすい。現状は約 50字 |
| B2 | 見出し階層。節見出し（h3）を左縦棒から「太字 18〜19px、上余白大」に変え、h1 30px、副題 16.5px 灰色 | `styles.css` | 縦棒は図のキャプションや引用の縦線と競合して目が散る |
| B3 | 前後ナビを `<nav class="chapter-nav">` に変換してカード状に。末尾ナビには次回の題名を添える（`series.json` から取れる） | `build.py`（`<!-- NAV:TOP -->` 〜 `<!-- /NAV -->` をラップ）、`styles.css` | 参考は blockquote を使うが、本リポジトリは NAV マーカーがあるので意味づけできる |
| B4 | 図版の枠。`img{width:min(100%,720px)}`、薄い枠線と角丸、中央。キャプションは 13.5px 灰色、中央、`max-width:620px`。`em{font-style:normal}` で斜体をやめる | `styles.css` | 本リポジトリの SVG は自前の紙色背景を持つので、枠は細線のみにして二重枠に見せない |
| B5 | ヘッダーを `position:sticky` にして半透明＋ぼかし。`scroll-padding-top` を合わせる | `styles.css` | 長い章で目次ボタンに戻りやすくなる |
| B6 | リスト・段落・区切り線の余白を参考値に寄せる（`p{margin:0 0 1.05em}`、`li{margin:0 0 .35em}`） | `styles.css` | 本文の密度が上がり、1画面に入る量が増える |

### 段階C　本リポジトリ固有の課題（参考にない対応）

| # | 内容 | 変更場所 | 補足 |
| --- | --- | --- | --- |
| C1 | 電話幅で図の文字が読めない問題。候補は三つ。(a) 600px 以下では図を横スクロール容器に入れ、`img{min-width:640px}` で縮小率を抑える。(b) 図を `<a href="…svg">` で包み、タップで原寸の SVG を開けるようにする。(c) `draw_figures.py` の文字サイズを一段大きくして再生成する。**まず (a)＋(b) を採り、(c) は見送る**（再生成は全51図に及び、レイアウト調整が大きい） | `build.py`、`styles.css` | 参考も縮小自体は避けていないが、参考の SVG は文字が大きい |
| C2 | 目次ドロワーを部で区切る。`series.json` に `parts: [{number, title, chapters:[lo,hi]}]` を足し、ドロワーに `第I部 意味は分布である` のような見出しを入れる。第2クールも同様 | `series.json`、`series-2/series.json`、`build.py`、`styles.css` | 参考の `cours` と同じ仕組み。連載設計書の4部構成がそのまま使える |
| C3 | 単独ファイル版（`complete.html`）にも A1・A3・B1〜B4 が効くことを確認する。`make_book` は `render` を通るので自動で反映されるが、`.book` の幅（860px）を 720px に揃える | `build.py` | |

### やらないこと

- 数式まわり（参考 `8274ba0`）。本リポジトリは数式を使わない。
- `autolink_bare_uris`（参考 `318588c`）。参考文献は全て明示リンクで、`::` を含む DOI の扱いを増やす理由がない。
- JavaScript の導入。参考と同じく CSS のみで実装する。
- 図の再生成（C1 の (c)）。効果に対して変更範囲が大きいので、A〜C を当てたあとに電話幅で再評価して決める。

## 4. 進め方と検証

1. 段階A を一つのコミットで。`validate.py`・テスト・`build.py`・`check_html.py` を通し、A1 は `check_html.py` の新しい検査で担保する。
2. 段階B を一つのコミットで。CSS の数値は参考をそのまま使い、本リポジトリの色（藍・深緑）だけ残す。
3. 段階C は C1 → C2 → C3 の順に、それぞれ別コミット。
4. 各段階のあとに、デスクトップ幅・電話幅（375px）・ダークモードの三つで、トップ、第1クール第5回（図4枚）、第2クール第9回（図2枚、共通例 v3）、トップの目次表、単独ファイル版を目視する。参考と同じ章構成の比較用に、参考サイトの第4回（表と図が多い）を隣に開く。
5. `guides/READING.md` と `CHANGELOG.md` に、行長・図の扱い・電話幅での図の開き方を一行ずつ記す。

## 5. 影響範囲

| ファイル | 段階 |
| --- | --- |
| `scripts/build.py` | A1・A2・A3・B3・C1・C2・C3 |
| `scripts/check_html.py` | A1 |
| `site-src/styles.css` | A3・A4・B1〜B6・C1・C2 |
| `series.json`、`series-2/series.json` | C2 |
| `tests/test_repository.py` | A1（図とキャプションの検査）、C2（parts の整合） |
| `guides/READING.md`、`CHANGELOG.md` | 4 |

本文（`chapters/`、`series-2/chapters/`）と SVG は変更しない。
