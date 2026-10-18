# GitHub登録とPages公開

[連載目次へ](../README.md)

## 現在の状態

この作業環境ではローカルの `git init` と初期コミットまでを行い、GitHubへの新規作成・push・Pages配置は実施していない。以下は手元の認証済みGitHub CLIを用いて実行する手順である。

Git、GitHub CLI、Python 3.11以降、Pandoc 3.xを準備する。GitHub CLIは[公式マニュアル](https://cli.github.com/manual/gh_repo_create)に従って導入・認証する。トークンを原稿・設定・コマンド引数へ貼り付けない。

```sh
gh auth status
git config --get user.name
git config --get user.email
```

## 新規リポジトリを作成する

最初に計画だけを確認できる。

```sh
python scripts/publish.py --owner yamaguchiyoshito --name relevance
```

非公開の新規リポジトリを作り、現在のブランチをpushする場合は、明示的に `--execute` を付ける。

```sh
python scripts/publish.py --owner yamaguchiyoshito --name relevance --visibility private --execute
```

既定は `private` である。未コミットの変更、既存のリモート、同名の既存リポジトリがあれば停止する。force push、既存ファイルの上書き、公開範囲の変更は行わない。生成物 `_site/` とPythonキャッシュは `.gitignore` により登録されない。

公開する判断を行った場合のみ `--visibility public` を指定する。GitHub Pagesは公開リポジトリでは無料で使える。非公開リポジトリでのPages利用は契約に依存する。

## GitHub Pagesを有効にする

リポジトリの Settings → Pages → Build and deployment で Source を **GitHub Actions** にする。以後、`main` へのpushごとに `.github/workflows/pages.yml` が検査・ビルド・配置を行う。初回は Actions タブから `Publish to GitHub Pages` を手動実行してもよい。

配置されるのは `_site/` の読者用出力である。Markdown原本、スクリプト、テストはサイトへ配置しない。公開URLは実際に成功したPagesジョブの `github-pages` 環境から取得する。推測した公開URLを案内しない。

## 公開前に決めること

- **ライセンス。** 本文と図のライセンスは未設定である。`LICENSE` を追加し、READMEの記述を更新する。
- **引用の範囲。** 第10回のケン・リュウからの引用は要約であり原文の転載ではない。公開前に再確認する。
- **参考文献の確認範囲。** `references/sources.json` の `checked` は書誌のみ確認の資料が多い。公開前に主要な出典を原文で照合する。

## CI設定の保守

検証ワークフローは `contents: read` のみとし、公開ジョブにのみ `pages: write` と `id-token: write` を与える。Pandocはローカル検証に使った3.7.0.2へ固定した。GitHub Actionsの主要バージョンは作成時点の公開情報に基づく。ワークフロー定義を同梱していることと、GitHub上でその実行が成功済みであることは区別する。この版のリモート実行は未実施である。

## 途中で失敗した場合

認証・ネットワーク・権限により、リポジトリ作成またはpushが失敗することがある。`gh repo create --source --push` はリモートを自動削除して取り消さない。GitHub上に空のリポジトリができているかを確認し、対象が空であると確認した場合に限り、通常の `git push -u origin main` で再開する。既存コンテンツのあるリポジトリへ強制pushしない。
