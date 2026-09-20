#!/usr/bin/env python3
"""貼文格式檢查。

教學重點：skill 的 scripts/ 是放「讓程式做比讓模型猜更可靠」的事——
數字數、算標籤數、抓違禁字。模型數中文字數會出錯，正規表達式不會。

用法：
    python3 check_post.py <貼文檔案路徑>

退出碼 0 = 全過，1 = 有問題（訊息印在 stdout）。
"""

import re
import sys
from pathlib import Path

BANNED = ["治癒", "根治", "療效", "保證", "100%", "絕對", "醫療", "治病", "藥效"]
LOCAL_KEYWORDS = ["鹿港", "天后宮"]

LIMITS = {
    "鉤子": (1, 15),
    "內文": (80, 150),
    "圖卡文字": (1, 30),
}


def count_chars(text: str) -> int:
    """算實際字數：去掉空白與 emoji 之外的標點照算。"""
    return len(re.sub(r"\s", "", text))


def split_posts(raw: str) -> list[str]:
    """用【鉤子】當分隔點，把多篇切開。"""
    parts = re.split(r"(?=【鉤子】)", raw)
    return [p for p in parts if "【鉤子】" in p]


def check_post(post: str, index: int) -> list[str]:
    problems: list[str] = []
    label = f"第 {index} 篇"

    fields = dict(re.findall(r"【(.+?)】(.*?)(?=【|\Z)", post, re.S))

    for name, (lo, hi) in LIMITS.items():
        if name not in fields:
            problems.append(f"{label}：缺少【{name}】")
            continue
        n = count_chars(fields[name])
        if not lo <= n <= hi:
            problems.append(f"{label}【{name}】{n} 字，應在 {lo}–{hi} 字之間")

    if "CTA" not in fields:
        problems.append(f"{label}：缺少【CTA】")

    tags = re.findall(r"#[^\s#]+", fields.get("Hashtag", ""))
    if not 8 <= len(tags) <= 12:
        problems.append(f"{label}：hashtag {len(tags)} 個，應為 8–12 個")

    for word in BANNED:
        if word in post:
            problems.append(f"{label}：出現違禁字「{word}」")

    if not any(k in post for k in LOCAL_KEYWORDS):
        problems.append(f"{label}：沒有提到 {' 或 '.join(LOCAL_KEYWORDS)}，本地搜尋吃不到")

    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"找不到檔案：{path}")
        return 1

    posts = split_posts(path.read_text(encoding="utf-8"))
    if not posts:
        print("沒有偵測到任何貼文（找不到【鉤子】區塊）")
        return 1

    problems = []
    for i, post in enumerate(posts, start=1):
        problems.extend(check_post(post, i))

    if problems:
        print(f"✗ {len(posts)} 篇中發現 {len(problems)} 個問題：")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"✓ {len(posts)} 篇全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
