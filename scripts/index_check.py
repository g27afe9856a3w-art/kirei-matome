"""Search Console URL検査APIで、各記事がGoogleにインデックスされているかを確認する。

環境変数（weekly_report.py と同じ）:
- GOOGLE_APPLICATION_CREDENTIALS: サービスアカウントJSONのパス
- SC_SITE_URL: Search Console のプロパティ（例: sc-domain:kirei-matome.com）

出力: reports/index-status-YYYY-MM-DD.md
"""
import os
import re
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

SITE = "https://kirei-matome.com/"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
JST = timezone(timedelta(hours=9))

# coverageState の日本語訳（Search Console画面の表記に合わせる）
COVERAGE_JA = {
    "Submitted and indexed": "✅ 登録済み（sitemap送信済み）",
    "Indexed, not submitted in sitemap": "✅ 登録済み（sitemap外）",
    "Crawled - currently not indexed": "⚠️ クロール済み・未登録",
    "Discovered - currently not indexed": "⚠️ 発見済み・未クロール",
    "URL is unknown to Google": "❌ Googleが存在を知らない",
    "Duplicate without user-selected canonical": "⚠️ 重複（正規URL未指定）",
    "Duplicate, Google chose different canonical than user": "⚠️ 重複（Googleが別URLを正規と判断）",
    "Alternate page with proper canonical tag": "ℹ️ 代替ページ",
    "Excluded by ‘noindex’ tag": "❌ noindexで除外",
    "Blocked by robots.txt": "❌ robots.txtでブロック",
    "Page with redirect": "ℹ️ リダイレクト",
    "Not found (404)": "❌ 404",
    "Soft 404": "❌ ソフト404",
    "Server error (5xx)": "❌ サーバーエラー",
}


def target_urls() -> list[str]:
    # Python標準のUser-AgentだとCloudflareに403で弾かれるため名乗る
    req = urllib.request.Request(SITE + "sitemap.xml",
                                 headers={"User-Agent": "Mozilla/5.0 (kirei-matome index-check)"})
    xml = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    posts = sorted({u for u in locs if "/posts/" in u and u.rstrip("/") != SITE + "posts"})
    return [SITE] + posts


def main() -> int:
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    site_url = os.environ.get("SC_SITE_URL")
    if not creds_path or not site_url:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS / SC_SITE_URL 必須", file=sys.stderr)
        return 1

    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    urls = target_urls()
    rows, errors = [], []
    for url in urls:
        try:
            res = service.urlInspection().index().inspect(
                body={"inspectionUrl": url, "siteUrl": site_url, "languageCode": "ja"}
            ).execute()
            r = res.get("inspectionResult", {}).get("indexStatusResult", {})
            rows.append({
                "url": url,
                "verdict": r.get("verdict", "?"),
                "coverage": r.get("coverageState", "?"),
                "last_crawl": (r.get("lastCrawlTime") or "")[:10],
                "fetch": r.get("pageFetchState", ""),
                "robots": r.get("robotsTxtState", ""),
                "google_canonical": r.get("googleCanonical", ""),
            })
        except Exception as e:  # 1件の失敗で全体を止めない
            errors.append((url, str(e)[:200]))
        time.sleep(1.2)  # 600件/分の上限に余裕を持たせる

    today = datetime.now(JST).strftime("%Y-%m-%d")
    indexed = [r for r in rows if r["verdict"] == "PASS"]
    mark = {"PASS": "✅", "NEUTRAL": "⚠️", "FAIL": "❌"}
    label = lambda r: f'{mark.get(r["verdict"], "")} {COVERAGE_JA.get(r["coverage"], r["coverage"])}'.strip()
    cov = Counter(label(r) for r in rows)

    out = [f"# インデックス状況（{today}）", "",
           "Search Console URL検査APIによる取得。`scripts/index_check.py` が自動生成。", "",
           "## サマリー", "",
           f"- 検査したURL: **{len(urls)}**（トップ + 記事）",
           f"- **Googleに登録済み: {len(indexed)} / {len(rows)}**",
           f"- 取得エラー: {len(errors)}", "",
           "| 状態 | 件数 |", "|---|---:|"]
    out += [f"| {k} | {v} |" for k, v in cov.most_common()]
    out += ["", "## URL別", "",
            "| URL | 状態 | 最終クロール | 取得 |", "|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: (x["verdict"] == "PASS", x["url"])):
        path = r["url"].replace(SITE.rstrip("/"), "") or "/"
        out.append(f"| `{path}` | {label(r)} "
                   f"| {r['last_crawl'] or '未クロール'} | {r['fetch']} |")
    if os.environ.get("SUBMIT_SITEMAP") == "1":
        out += ["", "## sitemap の再送信", ""]
        try:
            wcreds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/webmasters"])
            wservice = build("searchconsole", "v1", credentials=wcreds, cache_discovery=False)
            wservice.sitemaps().submit(siteUrl=site_url, feedpath=SITE + "sitemap.xml").execute()
            out.append(f"✅ `{SITE}sitemap.xml` を再送信しました（{today}）。Googleが読み直すまで数日かかることがあります。")
        except Exception as e:
            out.append(f"❌ 再送信に失敗: {str(e)[:300]}")
            out.append("（サービスアカウントに Search Console の『フル』権限が無い場合に起きる。画面から手動で再送信できる）")

    out += ["", "## Search Console に送信済みの sitemap", ""]
    try:
        sm = service.sitemaps().list(siteUrl=site_url).execute().get("sitemap", [])
        if not sm:
            out.append("**送信済みの sitemap がありません。**")
        else:
            out += ["| sitemap | 最終送信 | Googleの最終読込 | 状態 | エラー | 警告 | 送信URL数 |",
                    "|---|---|---|---|---:|---:|---:|"]
            for m in sm:
                submitted = sum(int(c.get("submitted", 0)) for c in m.get("contents", []))
                out.append(f"| `{m.get('path')}` | {(m.get('lastSubmitted') or '')[:10]} "
                           f"| {(m.get('lastDownloaded') or '未読込')[:10]} "
                           f"| {'処理待ち' if m.get('isPending') else '処理済み'} "
                           f"| {m.get('errors', 0)} | {m.get('warnings', 0)} | {submitted} |")
    except Exception as e:
        out.append(f"取得エラー: {str(e)[:200]}")

    if errors:
        out += ["", "## 取得エラー", ""] + [f"- `{u}`: {e}" for u, e in errors]

    os.makedirs("reports", exist_ok=True)
    path = f"reports/index-status-{today}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {path}: indexed {len(indexed)}/{len(rows)}, errors {len(errors)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
