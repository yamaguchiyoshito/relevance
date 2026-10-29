# 編集・保守ガイド

[連載目次へ](../README.md)

## 原本と生成物の責務

| パス | 責務 | 編集方法 |
| --- | --- | --- |
| `chapters/*.md` | 各回の本文、図の参照とキャプション、脚注、前後リンク | 直接編集する |
| `series.json` | 第1クールの順序、題名、副題、概要、部（`parts`）、各回の図の一覧（`figures`）と出典の対応 | 本文変更と同じPRで整合させる |
| `series-2/series.json`、`series-2/README.md`、`series-2/chapters/*.md` | 第2クールの正本、目次、本文 | 第1クールと同じ規則。図と出典は未着手なので `figures`・`sources` は空 |
| `assets/illustrations/*.svg` | 本文から参照する独立した挿絵 | `draw_figures.py` を編集して再生成する |
| `scripts/draw_figures.py` | 表紙と各回の図（計29点）を再現する図形コード | 原則としてこちらを編集する |
| `references/sources.json` | 文献の書誌と今回の確認範囲 | 一次情報と確認状況を分けて更新する |
| `references/bibliography.md` | 読者向けの文献一覧 | `scripts/bibliography.py` で再生成する |
| `guides/SERIES-DESIGN.md` | 連載の設計書（各回の核となる主張、素材対応表） | 構成を変えるときに更新する |
| `site-src/styles.css` | HTML閲覧用の見た目 | 本文内容を持たせない |
| `scripts/build.py` | MarkdownをHTMLへ変換 | 原本を改変しない |
| `scripts/validate.py` | 本文・参照・SVG・出典の構造検査 | 検査規則を保守する |
| `scripts/check_html.py` | HTMLの相対リンク・アンカー・外部依存を検査 | 生成後に実行する |
| `tests/` | 検査・変換の回帰試験 | 成功例と失敗例を両方持つ |
| `scripts/publish.py` | 新規GitHubリポジトリ作成の補助 | 既存リポジトリには使わない |
| `_site/` | ブラウザ用生成物 | 直接編集せず再生成する |

## 変更の最小手順

```sh
# Markdown、図の生成コード、出典を編集した後
python scripts/draw_figures.py
python scripts/bibliography.py
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build.py
python scripts/check_html.py
```

SVGを直接修正すると次の図再生成で上書きされる。長期保守する変更は `draw_figures.py` に反映する。各連載は全12回の枠組みを固定し、追加の連載は `series-N/` に自分の `series.json` と目次を持つ別シリーズとして加え、`scripts/build.py` の `SERIES_FILES` に登録する。

## 各回の型

各回は次の順で構成する。冒頭の違和感（日常的な場面か短い問い）、核となる主張（1回につき1文で言い切れる主張を1つ）、LLMと人間を対照する「鏡」の節、次回への橋。本文は2,000〜2,500字を目安とし、最終回のみ総括として長い。

回をまたぐリフレインは三つある。「関連は仮説に過ぎない」（6・10・12回）、「境界は明確か」（2・10・12回）、「中にある／間にある」（5・12回）。改稿するときはこれらの位置と文言を崩さない。

## 図の置き方と密度

図は、その内容を説明し終えた段落の直後に置く。次の節や二つ先の節の内容を先に見せる図は、分割して該当する節へ移す。1枚につき主張は1つ、パネルは2枚まで、ラベル文は10個前後までとする。1回あたりの枚数に上限はないが、4枚を超えるなら本文側の説明を疑う。

ファイル名は `NN-x-slug.svg`（回番号と枝番）とし、各連載の `series.json` の `figures` に本文での登場順に並べる。第2クール以降の図は `assets/illustrations/<連載id>/` のサブフォルダに置き、見出しラベルと主色を連載ごとに変える（第1クールは藍、第2クールは深緑）。Markdownから `![代替テキスト](../assets/illustrations/05-a-sea-and-summer.svg)` のように相対参照し、直後に `*図N-k：前提の説明*` というキャプションを置く。`k` は回内の通し番号で、検査は `figures` の数と順序に一致することを確かめる。SVGコードを本文へ貼り付けない。

SVGには `viewBox`、`role="img"`、`title`、`desc` を持たせる。`script`、`foreignObject`、外部画像、外部フォント、イベントハンドラは入れない。グラデーションなど `url(#id)` による内部参照は許す。矢印や色だけに意味を依存させず、ラベルでも区別する。日本語の表示は閲覧環境のフォントを利用し、フォントファイルは同梱しない。

## 部の扉絵

各部の最初の回には、副題と冒頭の前後ナビの直後に扉絵を一枚置く。扉絵は文字を持たない象徴図で、見出しラベルも図番号もキャプションも持たない。大きさは 1200×360、ファイル名は `NN-0-opener.svg`、各連載の `series.json` では章の `figures` ではなく `parts[].opener` に登録する。本文からは `![代替テキスト](../assets/illustrations/01-0-opener.svg){.opener}` のように `{.opener}` を付けて参照し、ビルドは枠・スクロール容器・原寸リンクを付けずに全幅で表示する。検査は、各部に扉絵が一枚あり、該当回の最初の節より前で参照されていることを確かめる。扉絵も `draw_figures.py` から生成する。

## 連載単位の図

表紙、見取り図、連載の関係図、凡例、付録の図のように、章の図でも扉絵でもない図は、各連載の `series.json` の `extras` に登録する。検査は SVG の総数を「章の図＋扉絵＋extras」として数え、`extras` のファイルが存在することを確かめる。これらも `draw_figures.py` から生成する。

## 出典の管理

文献は本文の脚注 `[^young]` と末尾の「参考文献・注記」の脚注定義でつなぐ。同じIDを `sources.json` と `series.json` の `sources` でも使う。検査は、脚注の使用と定義、`series.json` の一覧、`sources.json` の存在が一致することを確かめる。

機械検査はURLの構文とローカル参照を検査する。外部URLの生存や、文献が主張を本当に支えるかは編集レビューで確認する。原典の語句を引用する場合は、引用符、引用範囲、ページを明示し、長文転載はしない。

## 公開前の目視確認

GitHubのPreview、HTMLのデスクトップ幅とスマートフォン幅で確認する。ページ全体の横はみ出し、欠けた日本語、切れた図の文字は修正する。
