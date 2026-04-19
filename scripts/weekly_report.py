"""週次レポート生成スクリプト.

GA4 Data API と Search Console API から過去7日分のデータを取得し、
reports/YYYY-MM-DD-weekly.md にリライト候補リストを含むレポートを書き出す。

必要な環境変数:
- GA_PROPERTY_ID: GA4 プロパティID（数値、例: 123456789）
- SC_SITE_URL: Search Console のサイトURL（例: sc-domain:kirei-matome.com）
- GOOGLE_APPLICATION_CREDENTIALS: サービスアカウントJSONのパス
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from googleapiclient.discovery import build
from google.oauth2 import service_account

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
KEYWORDS_CSV = REPO_ROOT / "keywords.csv"

SC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def fetch_ga4(property_id: str, start: str, end: str) -> list[dict]:
    client = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name="pagePath")],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="activeUsers"),
            Metric(name="averageSessionDuration"),
        ],
        limit=1000,
    )
    res = client.run_report(req)
    rows = []
    for row in res.rows:
        rows.append({
            "path": row.dimension_values[0].value,
            "views": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
            "avg_duration": float(row.metric_values[2].value),
        })
    return rows


def fetch_search_console(site_url: str, start: str, end: str, creds_path: str) -> list[dict]:
    creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SC_SCOPES)
    service = build("searchconsole", "v1", credentials=creds)
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["page", "query"],
        "rowLimit": 5000,
    }
    res = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    rows = []
    for r in res.get("rows", []):
        rows.append({
            "page": r["keys"][0],
            "query": r["keys"][1],
            "clicks": r["clicks"],
            "impressions": r["impressions"],
            "ctr": r["ctr"],
            "position": r["position"],
        })
    return rows


def load_keywords() -> dict[str, dict]:
    if not KEYWORDS_CSV.exists():
        return {}
    with KEYWORDS_CSV.open() as f:
        return {row["slug"]: row for row in csv.DictReader(f)}


def extract_slug(path: str) -> str:
    parts = [p for p in path.split("/") if p]
    return parts[-1] if parts else ""


def identify_rewrite_candidates(ga_rows: list[dict], sc_rows: list[dict]) -> list[dict]:
    """リライト候補を抽出: 11-20位の記事 or 低CTR記事 or PV急落."""
    by_page: dict[str, dict] = {}
    for r in sc_rows:
        page = r["page"]
        b = by_page.setdefault(page, {
            "page": page, "clicks": 0, "impressions": 0,
            "positions": [], "top_queries": [],
        })
        b["clicks"] += r["clicks"]
        b["impressions"] += r["impressions"]
        b["positions"].append(r["position"])
        b["top_queries"].append((r["query"], r["clicks"], r["impressions"], r["position"]))

    ga_by_slug = {extract_slug(r["path"]): r for r in ga_rows}

    candidates = []
    for page, d in by_page.items():
        if not d["positions"]:
            continue
        avg_pos = sum(d["positions"]) / len(d["positions"])
        ctr = d["clicks"] / d["impressions"] if d["impressions"] else 0
        slug = extract_slug(page)
        reasons = []
        if 11 <= avg_pos <= 20 and d["impressions"] >= 50:
            reasons.append(f"順位{avg_pos:.1f}位（10位台/あと一歩）")
        if ctr < 0.02 and d["impressions"] >= 100:
            reasons.append(f"CTR {ctr:.1%}（低い・タイトル/ディスクリ改善余地）")
        if reasons:
            d["top_queries"].sort(key=lambda x: -x[2])
            candidates.append({
                "slug": slug,
                "page": page,
                "avg_position": avg_pos,
                "ctr": ctr,
                "clicks": d["clicks"],
                "impressions": d["impressions"],
                "ga_views": ga_by_slug.get(slug, {}).get("views", 0),
                "reasons": reasons,
                "top_queries": d["top_queries"][:5],
            })
    candidates.sort(key=lambda c: -c["impressions"])
    return candidates


def write_report(ga_rows: list[dict], sc_rows: list[dict], start: str, end: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    kw = load_keywords()
    candidates = identify_rewrite_candidates(ga_rows, sc_rows)

    ga_total_views = sum(r["views"] for r in ga_rows)
    ga_top10 = sorted(ga_rows, key=lambda r: -r["views"])[:10]
    sc_total_clicks = sum(r["clicks"] for r in sc_rows)
    sc_total_impressions = sum(r["impressions"] for r in sc_rows)

    out = REPORTS_DIR / f"{end}-weekly.md"
    with out.open("w") as f:
        f.write(f"# 週次レポート {start} 〜 {end}\n\n")
        f.write("## サマリー\n\n")
        f.write(f"- 合計PV（GA4）: **{ga_total_views:,}**\n")
        f.write(f"- 合計クリック（SC）: **{sc_total_clicks:,}**\n")
        f.write(f"- 合計表示回数（SC）: **{sc_total_impressions:,}**\n")
        f.write(f"- リライト候補: **{len(candidates)}件**\n\n")

        f.write("## PV TOP 10（GA4）\n\n")
        f.write("| 順位 | パス | PV | UU |\n|---|---|---:|---:|\n")
        for i, r in enumerate(ga_top10, 1):
            f.write(f"| {i} | `{r['path']}` | {r['views']:,} | {r['users']:,} |\n")
        f.write("\n")

        f.write("## 🔧 リライト候補（優先度順）\n\n")
        if not candidates:
            f.write("_該当なし_\n\n")
        for c in candidates:
            meta = kw.get(c["slug"], {})
            primary = meta.get("primary_keyword", "-")
            f.write(f"### `{c['slug']}`\n\n")
            f.write(f"- 狙いキーワード: **{primary}**\n")
            f.write(f"- 平均順位: {c['avg_position']:.1f} / CTR: {c['ctr']:.2%}\n")
            f.write(f"- クリック: {c['clicks']} / 表示: {c['impressions']} / PV(GA4): {c['ga_views']}\n")
            f.write(f"- 理由: {' / '.join(c['reasons'])}\n")
            f.write("- 上位流入クエリ:\n")
            for q, clk, imp, pos in c["top_queries"]:
                f.write(f"  - `{q}` — 表示{imp} / クリック{clk} / 順位{pos:.1f}\n")
            f.write(f"- 🤖 Claude Code指示例: `{c['slug']}.md をリライトして。主軸KW「{primary}」で、上記クエリを見出しに入れて強化`\n\n")

        f.write("## 📝 新規記事候補\n\n")
        f.write("_Search Consoleで表示回数はあるが自サイト記事がないクエリ_\n\n")
        existing_slugs = {extract_slug(r["page"]) for r in sc_rows}
        orphan_queries: dict[str, dict] = {}
        for r in sc_rows:
            if r["position"] > 30:
                orphan_queries.setdefault(r["query"], {"impressions": 0, "clicks": 0, "positions": []})
                orphan_queries[r["query"]]["impressions"] += r["impressions"]
                orphan_queries[r["query"]]["clicks"] += r["clicks"]
                orphan_queries[r["query"]]["positions"].append(r["position"])
        orphans = sorted(orphan_queries.items(), key=lambda x: -x[1]["impressions"])[:15]
        f.write("| クエリ | 表示 | クリック | 平均順位 |\n|---|---:|---:|---:|\n")
        for q, d in orphans:
            pos = sum(d["positions"]) / len(d["positions"])
            f.write(f"| {q} | {d['impressions']} | {d['clicks']} | {pos:.1f} |\n")
        f.write("\n")

    return out


def main() -> int:
    prop = os.environ.get("GA_PROPERTY_ID")
    site = os.environ.get("SC_SITE_URL")
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not (prop and site and creds):
        print("ERROR: GA_PROPERTY_ID / SC_SITE_URL / GOOGLE_APPLICATION_CREDENTIALS 必須", file=sys.stderr)
        return 1
    end = date.today()
    start = end - timedelta(days=7)
    s, e = start.isoformat(), end.isoformat()
    print(f"Fetching GA4 {s} - {e} ...")
    ga_rows = fetch_ga4(prop, s, e)
    print(f"Fetching Search Console {s} - {e} ...")
    sc_rows = fetch_search_console(site, s, e, creds)
    out = write_report(ga_rows, sc_rows, s, e)
    print(f"Wrote {out}")
    # GitHub Actions で後続ステップに渡す
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"report_path={out.relative_to(REPO_ROOT)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
