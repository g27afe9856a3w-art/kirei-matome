#!/usr/bin/env python3
"""
アイキャッチ画像生成スクリプト（libeblog 原則準拠）
- 1280x720 (16:9)
- パワーワード + 数字を大きく
- 半透明バンドで可読性確保
- ヒラギノ角ゴシック W8
"""
import subprocess
import os
from pathlib import Path

BASE = Path("/Users/kataokahirokazu/Documents/affiliate-blog/kirei-matome")
EYECATCH_DIR = BASE / "static/images/eyecatch"

FONT_BOLD = "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"
FONT_MED = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"

# 記事ごとの設定: slug -> (背景画像, メインコピー, サブコピー, アクセント色)
# メインは 18文字以内推奨・数字とパワーワード必須
ARTICLES = {
    # 脱毛
    "datsumo-clinic-ranking":    ("bg-beauty.jpeg",    "脱毛クリニック\nおすすめTOP5", "医療脱毛を徹底比較",         "#e8637a"),
    "datsumo-price-guide":       ("bg-beauty.jpeg",    "全身脱毛\n料金相場2026",     "最安値クリニックは？",       "#e8637a"),
    "datsumo-salon-vs-clinic":   ("bg-beauty.jpeg",    "サロンvs医療\n徹底比較",      "どっちが得？",               "#e8637a"),
    "datsumo-student-guide":     ("bg-beauty.jpeg",    "学生脱毛\n月2,800円〜",       "学割で賢く選ぶ",             "#e8637a"),
    "mens-datsumo-ranking":      ("bg-mens.jpeg",      "メンズ脱毛\nおすすめTOP5",     "清潔感をアップ",             "#3498db"),
    "vio-datsumo-guide":         ("bg-beauty.jpeg",    "VIO脱毛\n完全ガイド",         "痛み・料金・期間",           "#e8637a"),
    "20s-datsumo-guide":         ("bg-beauty.jpeg",    "20代の脱毛\nベスト選び",       "月3,000円〜で始める",        "#e8637a"),

    # 美容
    "skincare-ranking":          ("bg-beauty.jpeg",    "スキンケア\nおすすめTOP10",    "美肌を叶える",               "#e8637a"),
    "whitening-clinic-guide":    ("bg-whitening.jpeg", "ホワイトニング\nクリニック5選", "歯科で徹底比較",             "#6cb5d9"),
    "self-whitening-guide":      ("bg-whitening.jpeg", "セルフ\nホワイトニング",       "月3,000円〜でOK",            "#6cb5d9"),
    "mens-skincare-guide":       ("bg-mens.jpeg",      "メンズ\nスキンケア入門",       "3分で完結",                  "#3498db"),
    "aga-clinic-ranking":        ("bg-mens.jpeg",      "AGA治療\nおすすめTOP5",       "月4,400円〜で始める",        "#3498db"),
    "hair-care-ranking":         ("bg-beauty.jpeg",    "ヘアケア\nおすすめTOP10",     "ツヤ髪を叶える",             "#e8637a"),

    # 健康
    "protein-ranking":           ("bg-kenko.jpeg",     "女性プロテイン\nTOP10",       "ダイエット・美容に",         "#27ae60"),
    "diet-supplement-ranking":   ("bg-kenko.jpeg",     "ダイエット\nサプリTOP10",     "科学的に選ぶ",               "#27ae60"),
    "collagen-supplement-ranking":("bg-beauty.jpeg",   "コラーゲン\nサプリTOP10",     "飲む美容液",                 "#e8637a"),
    "whitening-supplement-ranking":("bg-whitening.jpeg","美白サプリ\nおすすめTOP10",   "シミ・くすみ対策",           "#6cb5d9"),
    "vitamin-c-supplement-ranking":("bg-kenko.jpeg",   "ビタミンC\nサプリTOP10",      "美肌・美白効果",             "#e67e22"),

    # お金
    "credit-card-cashback":      ("bg-okane.jpeg",     "高還元クレカ\nおすすめTOP5",  "年間数万円お得に",           "#c0392b"),
    "credit-card-beauty-ranking":("bg-okane.jpeg",     "美容クレカ\nおすすめTOP5",    "美容特典つき",               "#e8637a"),
    "student-credit-card-ranking":("bg-okane.jpeg",    "学生クレカ\nおすすめTOP5",    "年会費無料で高還元",         "#c0392b"),
    "poikatsu-guide":            ("bg-okane.jpeg",     "ポイ活\n完全ガイド",          "月1万円稼ぐ方法",            "#c0392b"),
}

def generate(slug, bg, main, sub, accent):
    src = EYECATCH_DIR / bg
    dst = EYECATCH_DIR / f"eye-{slug}.jpeg"
    if not src.exists():
        print(f"  SKIP (no bg): {slug}")
        return False

    # 1. リサイズ＆クロップ 1280x720
    # 2. 左側に半透明グラデーションバンド（テキスト可読性）
    # 3. メインコピー（白文字・極太）
    # 4. サブコピー（白文字・中太）
    # 5. アクセント色の下線
    # 6. サイト名 "キレイまとめ" を右下に

    cmd = [
        "magick", str(src),
        "-resize", "1280x720^",
        "-gravity", "center",
        "-extent", "1280x720",
        # 左側に黒半透明オーバーレイ（テキスト領域）
        "(", "-size", "1280x720", "xc:none",
             "-fill", "rgba(0,0,0,0.55)",
             "-draw", "rectangle 0,0 780,720",
             "-blur", "0x30",
        ")", "-compose", "over", "-composite",
        # アクセント色の縦ライン
        "-fill", accent, "-draw", f"rectangle 60,100 68,620",
        # メインコピー（2行対応）
        "-font", FONT_BOLD,
        "-pointsize", "84",
        "-fill", "white",
        "-gravity", "NorthWest",
        "-annotate", "+100+140", main,
        # サブコピー
        "-font", FONT_MED,
        "-pointsize", "34",
        "-fill", "#ffd8e0",
        "-annotate", "+100+420", sub,
        # ブランド名（右下）
        "-font", FONT_MED,
        "-pointsize", "26",
        "-fill", "rgba(255,255,255,0.85)",
        "-gravity", "SouthEast",
        "-annotate", "+40+32", "💄 キレイまとめ",
        "-quality", "86",
        str(dst),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAIL: {slug}")
        print(result.stderr[:500])
        return False
    print(f"  OK: eye-{slug}.jpeg")
    return True

def main():
    success = 0
    for slug, (bg, main, sub, accent) in ARTICLES.items():
        if generate(slug, bg, main, sub, accent):
            success += 1
    print(f"\n{success}/{len(ARTICLES)} 枚生成完了")

if __name__ == "__main__":
    main()
