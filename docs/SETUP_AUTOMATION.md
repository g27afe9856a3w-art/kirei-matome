# 週次レポート自動化 セットアップ手順

GitHub Actions が毎週月曜 9:00 JST に GA4 + Search Console からデータを取得し、
リライト候補・新規記事候補を Issue として通知します。

---

## 1. Google Cloud プロジェクト + サービスアカウント作成

### 1-1. プロジェクト作成

1. https://console.cloud.google.com/ にアクセス
2. 上部プロジェクト選択 → **新しいプロジェクト** → 名前「kirei-matome-analytics」→ 作成

### 1-2. API を有効化

以下2つを有効化します。

1. https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com → **有効にする**
2. https://console.cloud.google.com/apis/library/searchconsole.googleapis.com → **有効にする**

### 1-3. サービスアカウント作成

1. https://console.cloud.google.com/iam-admin/serviceaccounts → **サービスアカウントを作成**
2. 名前: `kirei-matome-reporter` → 作成して続行 → ロールはスキップ → 完了
3. 作成したサービスアカウントをクリック → **キー** タブ → **鍵を追加** → **新しい鍵を作成** → **JSON** → 作成
4. JSON ファイルがダウンロードされる（**この中身が後で必要**）
5. サービスアカウントの**メールアドレス**をコピー（例: `kirei-matome-reporter@xxx.iam.gserviceaccount.com`）

---

## 2. GA4 にサービスアカウントを追加

1. https://analytics.google.com/ → 左下⚙ **管理**
2. プロパティ列の **プロパティのアクセス管理** を開く
3. 右上 **+** → **ユーザーを追加**
4. メールアドレスにサービスアカウントのメールを貼り付け → ロール **閲覧者** → 追加

### GA4 プロパティ ID を確認

同じ管理画面の **プロパティの設定** → 右上に **プロパティ ID**（9桁の数字）が表示される。これをメモ。

---

## 3. Search Console にサービスアカウントを追加

1. https://search.google.com/search-console → プロパティ `kirei-matome.com` を選択
2. 左下⚙ **設定** → **ユーザーと権限** → **ユーザーを追加**
3. サービスアカウントのメールを貼り付け → 権限 **制限付き** → 追加

### Search Console の siteUrl

ドメインプロパティなので値は: `sc-domain:kirei-matome.com`

---

## 4. GitHub Secrets を登録

GitHub リポジトリ → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** で以下3つ登録。

| Name | Value |
|---|---|
| `GOOGLE_CREDENTIALS_JSON` | ダウンロードした JSON ファイルの**中身全部**（貼り付け） |
| `GA_PROPERTY_ID` | 手順 2 でメモした9桁の数字 |
| `SC_SITE_URL` | `sc-domain:kirei-matome.com` |

---

## 5. 動作確認

1. GitHub リポジトリ → **Actions** タブ → **Weekly Report** ワークフロー選択
2. **Run workflow** ボタンで手動実行
3. 完了後、**Issues** タブに「📊 週次レポート YYYY-MM-DD」が作成されれば成功
4. `reports/YYYY-MM-DD-weekly.md` もコミットされる

---

## 6. 以降の運用

- 毎週月曜朝、GitHub から Issue 通知メールが届く
- Issue 本文にリライト候補・新規記事候補が含まれる
- Claude Code を起動して **「最新の weekly-report Issue の候補を元にリライトして」** と頼めば作業開始

---

## トラブルシューティング

- **403 Permission denied**: GA4/SC にサービスアカウントを追加できていない
- **404 property not found**: `GA_PROPERTY_ID` が間違っている（URL の`p123…`ではなく管理画面のプロパティID）
- **siteUrl not found**: `sc-domain:` プレフィックスが抜けている
