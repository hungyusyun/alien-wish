#!/usr/bin/env python3
"""IG 發文格式檢查。

檢查的都是「程式算得準、模型會猜錯」的事：字數、秒數、標籤數、違規用詞。

用法：
    python3 check_post.py <檔案路徑> [--keyword 主關鍵字]

    --keyword  指定主關鍵字，會檢查它有沒有出現在文案首句（IG SEO 的關鍵位置）

退出碼 0 = 全過，1 = 有問題。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 硬性上限，依 references/playbook.md 的演算法規則
HASHTAG_RANGE = (3, 5)
FIRST_LINE_MAX = 40        # 文案首句，被「更多」截斷前的可見長度
HOOK_MAX = 25              # 鉤子要能當字卡，太長塞不下畫面
REELS_SECONDS = (7, 60)
MAX_SHOT_SECONDS = 4.0     # 單格畫面不換的上限
HOOK_DEADLINE = 1.5        # 第一格必須在這之前結束

BAD_OPENERS = ["大家好", "今天要來", "今天跟大家", "哈囉大家", "各位好", "我是"]

# 中國用語 → 台灣用語
CN_TERMS = {
    "視頻": "影片", "點贊": "按讚", "屏幕": "螢幕", "軟件": "軟體",
    "硬件": "硬體", "網絡": "網路", "博主": "版主／創作者", "內存": "記憶體",
    "信息": "資訊", "文件夾": "資料夾", "數據庫": "資料庫",
    "接口": "介面", "代碼": "程式碼", "視屏": "影片",
}

EMOJI_START = re.compile(r"^[\U0001F000-\U0001FAFF☀-➿]")
TIME_RANGE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:s|秒)?\s*[-–~～到]\s*(\d+(?:\.\d+)?)\s*(?:s|秒)?"
)


def visible_len(text: str) -> int:
    """算可見字數，空白不計。"""
    return len(re.sub(r"\s", "", text))


def split_posts(raw: str) -> list[str]:
    parts = re.split(r"^\s*──.*?──\s*$", raw, flags=re.M)
    posts = [p for p in parts if "【鉤子" in p]
    if posts:
        return posts
    # 沒有分隔線時，退而用第一個鉤子當起點，整份當一則
    return [raw] if "【鉤子" in raw else []


def parse_fields(post: str) -> dict[str, str]:
    """把【欄位】內容 抓成 dict，值取到下一個【為止。"""
    return {
        k.strip(): v.strip()
        for k, v in re.findall(r"【(.+?)】(.*?)(?=【|\Z)", post, re.S)
    }


def check_hooks(fields: dict[str, str], label: str) -> list[str]:
    problems = []
    hooks = {k: v for k, v in fields.items() if k.startswith("鉤子")}

    if len(hooks) < 3:
        problems.append(f"{label}：只有 {len(hooks)} 個鉤子變體，需要 3 個不同路線的")

    for name, text in hooks.items():
        body = re.sub(r"[（(].*?[）)]", "", text).strip()  # 去掉「（資訊差路線）」這種註記
        n = visible_len(body)
        if n > HOOK_MAX:
            problems.append(f"{label}【{name}】{n} 字，超過 {HOOK_MAX} 字會塞不進字卡")
        if not body:
            problems.append(f"{label}【{name}】是空的")
        for bad in BAD_OPENERS:
            if body.startswith(bad):
                problems.append(f"{label}【{name}】用「{bad}」開頭，會燒掉黃金 1.5 秒")
        if EMOJI_START.match(body):
            problems.append(f"{label}【{name}】用 emoji 開頭，emoji 不是鉤子")

    # 三個鉤子開頭雷同 = 沒有真的分路線
    openings = [visible_len(h) and re.sub(r"\s", "", h)[:6] for h in hooks.values()]
    openings = [o for o in openings if o]
    if len(openings) >= 2 and len(set(openings)) < len(openings):
        problems.append(f"{label}：鉤子開頭重複，三個變體要走不同路線，不是換句話說")

    return problems


def check_caption(fields: dict[str, str], label: str, keyword: str | None) -> list[str]:
    problems = []

    first = fields.get("文案首句", "")
    if not first:
        problems.append(f"{label}：缺少【文案首句】")
    else:
        n = visible_len(first)
        if n > FIRST_LINE_MAX:
            problems.append(
                f"{label}【文案首句】{n} 字，超過 {FIRST_LINE_MAX} 字會被「更多」截掉"
            )
        if keyword and keyword not in first:
            problems.append(f"{label}【文案首句】沒有出現主關鍵字「{keyword}」")

    if not fields.get("CTA"):
        problems.append(f"{label}：缺少【CTA】")
    elif not re.search(r"傳給|標|分享|留言|打上|存起來|收藏|私訊", fields["CTA"]):
        problems.append(
            f"{label}【CTA】沒有導向分享或留言，只叫人追蹤對觸及沒幫助"
        )

    tags = re.findall(r"#[^\s#]+", fields.get("Hashtag", ""))
    lo, hi = HASHTAG_RANGE
    if not lo <= len(tags) <= hi:
        problems.append(
            f"{label}：hashtag {len(tags)} 個，應為 {lo}–{hi} 個"
            f"{'（放太多會被降權）' if len(tags) > hi else ''}"
        )

    return problems


def check_reels(fields: dict[str, str], label: str) -> list[str]:
    """只在有【分鏡】時檢查。"""
    if "分鏡" not in fields:
        return []

    problems = []
    shots = []
    for line in fields["分鏡"].splitlines():
        m = TIME_RANGE.match(line)
        if m:
            shots.append((float(m.group(1)), float(m.group(2))))

    if not shots:
        problems.append(f"{label}【分鏡】抓不到任何時間段，格式應為「0.0–1.5s ｜畫面：…」")
        return problems

    if shots[0][1] > HOOK_DEADLINE:
        problems.append(
            f"{label}：第一格到 {shots[0][1]}s 才結束，鉤子必須在 {HOOK_DEADLINE}s 內出現"
        )

    for start, end in shots:
        if end - start > MAX_SHOT_SECONDS:
            problems.append(
                f"{label}：{start}–{end}s 這格 {end - start:.1f} 秒沒換畫面，上限 {MAX_SHOT_SECONDS} 秒"
            )

    total = shots[-1][1]
    lo, hi = REELS_SECONDS
    if not lo <= total <= hi:
        problems.append(f"{label}：總長 {total} 秒，應在 {lo}–{hi} 秒之間")

    declared = re.search(r"(\d+(?:\.\d+)?)", fields.get("總長", ""))
    if declared and abs(float(declared.group(1)) - total) > 0.5:
        problems.append(
            f"{label}：【總長】寫 {declared.group(1)} 秒，但分鏡只排到 {total} 秒"
        )

    return problems


def check_wording(post: str, label: str) -> list[str]:
    return [
        f"{label}：出現中國用語「{cn}」，應改成「{tw}」"
        for cn, tw in CN_TERMS.items()
        if cn in post
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--keyword", help="主關鍵字，檢查是否出現在文案首句")
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"找不到檔案：{args.path}")
        return 1

    posts = split_posts(args.path.read_text(encoding="utf-8"))
    if not posts:
        print("沒有偵測到任何貼文（找不到【鉤子】區塊）")
        return 1

    problems: list[str] = []
    for i, post in enumerate(posts, start=1):
        label = f"第 {i} 則"
        fields = parse_fields(post)
        problems += check_hooks(fields, label)
        problems += check_caption(fields, label, args.keyword)
        problems += check_reels(fields, label)
        problems += check_wording(post, label)

    if problems:
        print(f"✗ {len(posts)} 則中發現 {len(problems)} 個問題：")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"✓ {len(posts)} 則全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
