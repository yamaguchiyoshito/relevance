# 編集・保守ガイド

[連載目次へ](../README.md)

## 原本と生成物の責務

| パス | 責務 | 編集方法 |
| --- | --- | --- |
| `chapters/*.md` | 各回の本文、図の参照とキャプション、脚注、前後リンク | 直接編集する |
| `series.json` | 全12回の順序、題名、副題、概要、本文・図・出典の対応 | 本文変更と同じPRで整合させる |
| `assets/illustrations/*.svg` | 本文から参照する独立した挿絵 | `draw_figures.py` を編集して再生成する |
| `scripts/draw_figures.py` | 全13図を再現する図形コード | 原則としてこちらを編集する |
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

SVGを直接修正すると次の図再生成で上書きされる。長期保守する変更は `draw_figures.py` に反映する。全12回の枠組みは固定し、追加連載は別シリーズとして扱う。

## 各回の型

各回は次の順で構成する。冒頭の違和感（日常的な場面か短い問い）、核となる主張（1回につき1文で言い切れる主張を1つ）、LLMと人間を対照する「鏡」の節、次回への橋。本文は2,000〜2,500字を目安とし、最終回のみ総括として長い。

回をまたぐリフレインは三つある。「関連は仮説に過ぎない」（6・10・12回）、「境界は明確か」（2・10・12回）、「中にある／間にある」（5・12回）。改稿するときはこれらの位置と文言を崩さない。

## 図の記法

Markdownから `![代替テキスト](../assets/illustrations/01-reverse-engineering-meaning.svg)` のように相対参照し、直後に `*図N：前提の説明*` というキャプションを置く。SVGコードを本文へ貼り付けない。

SVGには `viewBox`、`role="img"`、`title`、`desc` を持たせる。`script`、`foreignObject`、外部画像、外部フォント、イベントハンドラは入れない。グラデーションなど `url(#id)` による内部参照は許す。矢印や色だけに意味を依存させず、ラベルでも区別する。日本語の表示は閲覧環境のフォントを利用し、フォントファイルは同梱しない。

## 出典の管理

文献は本文の脚注 `[^young]` と末尾の「参考文献・注記」の脚注定義でつなぐ。同じIDを `sources.json` と `series.json` の `sources` でも使う。検査は、脚注の使用と定義、`series.json` の一覧、`sources.json` の存在が一致することを確かめる。

機械検査はURLの構文とローカル参照を検査する。外部URLの生存や、文献が主張を本当に支えるかは編集レビューで確認する。原典の語句を引用する場合は、引用符、引用範囲、ページを明示し、長文転載はしない。

## 公開前の目視確認

GitHubのPreview、HTMLのデスクトップ幅とスマートフォン幅で確認する。ページ全体の横はみ出し、欠けた日本語、切れた図の文字は修正する。
