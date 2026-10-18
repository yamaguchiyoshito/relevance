# 変更履歴

## 1.0.0 — 2026-10-18

全12回の連載を、GitHub Pagesでの公開を前提とした独立したリポジトリとして整理した。スライド資料と単発エッセイ草稿から再構成した本文12本を `chapters/` に収め、前後ナビゲーション、各回一点の挿絵と図版キャプション、脚注による出典参照を加えた。

挿絵は表紙を含む13点のSVGで、`scripts/draw_figures.py` から決定論的に再生成できる。参考文献は `references/sources.json` を正本とし、`scripts/bibliography.py` で一覧を生成する。Pandocによる閲覧用HTMLのビルド、単一ファイル閲覧版、構造検査、回帰テスト、非公開を既定とするGitHub新規登録補助、`main` へのpushで動くPages配置ワークフローを実装した。

同日に `yamaguchiyoshito/relevance` を作成してpushし、公開リポジトリとしてGitHub Pages（GitHub Actionsソース）を有効化した。ライセンスは未設定である。
