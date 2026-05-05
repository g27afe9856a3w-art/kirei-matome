# 引き継ぎサマリー（キレイまとめ）

**日付**: 2026-05-06  
**サイト**: https://kirei-matome.com  
**リポジトリ**: https://github.com/g27afe9856a3w-art/kirei-matome (Private)

---

## 1. プロジェクト構成

| 項目 | 内容 |
|---|---|
| フレームワーク | Hugo 0.160.1+extended |
| テーマ | PaperMod（カスタマイズ済み） |
| ホスティング | Cloudflare Pages（mainブランチへのpushで自動デプロイ） |
| ドメイン | kirei-matome.com |
| アナリティクス | GA4: `G-SMMF5K60ZB` |
| Search Console | ドメインプロパティ |
| timeZone | `Asia/Tokyo`（hugo.tomlに記載・必須） |

**運営者**: 非エンジニアの個人ブロガー。専門用語を避けた平易な日本語で対応すること。

---

## 2. 自動化済みパイプライン

### 週次レポート自動化（稼働中）
- **トリガー**: GitHub Actions cron `0 0 * * 1`（毎週月曜 9:00 JST）
- **ファイル**: `.github/workflows/weekly-report.yml` / `scripts/weekly_report.py`
- **動作**: GA4 Data API + Search Console API → `reports/YYYY-MM-DD-weekly.md` 生成 → GitHub Issue自動起票
- **依存Secrets**: `GOOGLE_CREDENTIALS_JSON` / `GA_PROPERTY_ID` / `SC_SITE_URL`
- **キーワード管理**: `keywords.csv`（25記事のSEO戦略）

---

## 3. アフィリエイトASP状況

### A8.net
| プログラム | ステータス |
|---|---|
| エポスカード | ✅ 提携中（リンク挿入済み） |
| ルシアクリニック | ✅ 提携中 |
| RinRin（脱毛サロン） | ✅ 提携中 |
| リゼクリニック | ⏳ 申請中 |
| エミナルクリニック | ⏳ 申請中 |
| レジーナクリニック | ⏳ 申請中 |
| TCB東京中央美容外科 | ⏳ 申請中 |
| フレイアクリニック | ⏳ 申請中 |

### もしもアフィリエイト
| プログラム | ステータス | 報酬 | a_id |
|---|---|---|---|
| 楽天市場の商品購入 | ✅ **提携中** | 2.00% | 5508825 |
| 楽天カード・楽天プレミアムカード | ⏳ 申請中 | 2,800円/件 | - |
| Amazon.co.jp商品購入 | ⏳ 申請中 | 1.8% | - |

**もしもアフィリエイト 楽天市場の link format**:
```
https://af.moshimo.com/af/c/click?a_id=5508825&p_id=54&pc_id=54&pl_id=27059&url=【URL_ENCODED_RAKUTEN_URL】
```

---

## 4. 公開記事（24本）の現状

### アフィリエイトリンク挿入済み
- `summer-uv-care.md` — 楽天UV商品7点
- `collagen-supplement-ranking.md` — 楽天コラーゲン5点
- `whitening-supplement-ranking.md` — 楽天美白サプリ4点
- `face-datsumo-guide.md` — A8.net脱毛系（一部）
- `datsumo-clinic-ranking.md` — A8.netルシア
- `datsumo-salon-vs-clinic.md` — A8.netルシア・RinRin
- `credit-card-beauty-ranking.md` — エポスカードA8.net + 楽天カード`url="#"`待ち
- `credit-card-cashback.md` — 楽天カード`url="#"`待ち

### リンク未挿入（承認待ち or 未着手）
- `vitamin-c-supplement-ranking.md` — 商品ランキングなし、サプリ系リンク追加検討
- `mens-skincare-guide.md`
- `medical-diet-clinic.md`（公開直後）
- `whitening-clinic-guide.md`
- `vio-datsumo-guide.md`
- `skincare-ranking.md`

詳細は `data/affiliate_links.yaml` と `reports/affiliate-audit.md` を参照。

---

## 5. 開示・コンプライアンス対応済み

- `layouts/partials/extend_footer.html` に Amazonアソシエイト開示文
- `content/privacy-policy.md` に もしもアフィリエイト・Amazon開示
- `static/_redirects` に `/page/1/` → `/` の301（Search Console「代替ページ」対策）
- `wrangler.jsonc` の `preview_urls: false`（CLAUDE.md ルール準拠）

---

## 6. ショートコード仕様（重要・誤用注意）

| ショートコード | 形式 | 注意点 |
|---|---|---|
| `{{< cta url="..." text="..." sub="..." >}}` | 自己閉じ | **`/cta` で閉じてはいけない**（`.Inner`なし） |
| `{{< question q="..." a="..." >}}` | 自己閉じ | params のみ（`.Inner`なし） |
| `{{< point >}}…{{< /point >}}` | 開閉ペア | OK |
| `{{< caution >}}…{{< /caution >}}` | 開閉ペア | titleにスマートクォート禁止 |
| `{{< ranking num="1" name="..." >}}…{{< /ranking >}}` | 開閉ペア | OK |

---

## 7. 直近のTODO（優先順）

1. **楽天カード承認待ち** → 承認後、以下3箇所の `url="#"` を差し替え
   - `credit-card-beauty-ranking.md` の楽天カードCTA × 2
   - `credit-card-cashback.md` の楽天カードCTA × 1
2. **Amazon承認待ち** → 承認後、サプリ系記事5本にAmazonリンク追加
3. **A8.net 脱毛5社承認待ち** → `face-datsumo-guide.md` / `datsumo-clinic-ranking.md` に挿入
4. **vitamin-c-supplement-ranking.md** に商品ランキング・楽天リンク追加検討
5. 新記事候補: `keywords.csv` を見て未着手キーワード執筆

---

## 8. 開発ルール（CLAUDE.md より抜粋）

- **インフラ固定**: Next.js / Cloudflare Workers / D1 / Cloudflare Access / Claude Opus
- **GitHubは必ずPrivate**
- **APIキーは環境変数（Secrets）**
- **個人情報・決済情報を扱う案件はエンジニアに相談**
- **運営者は非エンジニア** — 平易な日本語、リスクは先回りで指摘

---

## 9. ローカル開発

```bash
cd /Users/kataokahirokazu/Documents/affiliate-blog/kirei-matome
hugo server -D            # -D で draft も表示
# → http://localhost:1313
```

ビルド確認: `hugo --quiet`（エラーなしなら出力なし）

---

## 10. 直近のコミット履歴

```
d0e3124 楽天市場アフィリエイトリンク挿入（もしもアフィリエイト 2%）
ccfe03f 公開: 医療ダイエットおすすめクリニック5選（draft→false）
d2f2aa4 fix: Amazon開示文追加 + ショートコードエラー全修正
ada4a29 feat(content): 医療ダイエット記事 + バグ修正2件
2408b30 chore: アフィリエイトリンク監査レポート + 管理ファイル更新
9b2e810 fix: questionショートコード修正 + /page/1/リダイレクト追加
497e42b feat: 週次レポート自動化（GA4+SC→Issue通知）
```

---

## 引き継ぎ先（Codex）への申し送り

このサイトは **収益化フェーズ**（記事公開→アフィリエイト最適化）に入っています。
- **記事追加よりも既存記事のリンク差し替え/最適化**を優先
- **承認メールが来たら**`data/affiliate_links.yaml` を参照して該当記事のCTAを更新
- **週次レポート（GitHub Issue）** を確認し、CTR低い記事のリライト or 順位11-20位記事の強化をする
- 非エンジニアの運営者なので、**勝手にインフラ変更しない**こと
