# 怎麼做一個 Skill

這個資料夾放的是**專案內的 skill**，會跟著 git 走，換電腦、分享給別人都還在。

## 目前有兩張

| Skill | 做什麼 | 狀態 |
|---|---|---|
| `ig-growth/` | IG 流量發文：Reels 分鏡、輪播圖卡、鉤子 A／B 測試 | **在用的** |
| `alien-post/` | 外星人祈願雞蛋糕的社群貼文 | 練手範例，留著當範本 |

### `ig-growth` 建議搬到全域

它跟這個 repo 沒關係，是通用工具。搬過去所有專案都能用：

```bash
cp -r .claude/skills/ig-growth ~/.claude/skills/
```

搬完重開 session。repo 裡這份留著當版控備份，改完記得兩邊同步
（或是反過來：全域放捷徑 `ln -s`，只維護 repo 這份）。

---

## 一、最小可跑的 Skill

一個資料夾 + 一個 `SKILL.md`，就這樣：

```
.claude/skills/你的名字/
└── SKILL.md
```

`SKILL.md` 必須長這樣：

```markdown
---
name: 你的名字
description: 做什麼。當使用者要…時使用。
---

# 標題

（這裡寫你每次都要重複交代的規則、流程、格式）
```

- `name` 只能小寫英數 + 連字號，**要跟資料夾名一模一樣**
- `description` 寫不好 = 永遠不會被觸發（見下面第三節）
- `---` 一定要在檔案第一行

## 二、要放專案內還是全域？

| 位置 | 誰能用 | 進 git | 適合 |
|---|---|---|---|
| `專案/.claude/skills/` | 只有這個專案 | ✅ | 跟這個生意／客戶綁定的 |
| `~/.claude/skills/` | 你所有專案 | ❌ | 通用工具（如寫作風格、n8n 產生器）|

搬過去只要 `cp -r .claude/skills/alien-post ~/.claude/skills/`。

## 三、`description` 是生死線

Claude 平常**只讀** `name` + `description` 來決定要不要載入這個 skill。
主文寫得再漂亮，description 爛就等於不存在。

❌ `description: 幫助使用者產生高品質內容`
　 → 太抽象，永遠不會觸發

✅ `description: 產出「外星人祈願雞蛋糕」的社群貼文文案（IG 貼文、限動、LINE 推播）。當使用者要寫貼文、限動、發文、宣傳刀療／易經／塔羅／祈願卡時使用。`
　 → 有具體產出物 + 有觸發時機 + 塞了你平常會講的詞

**公式**：`做什麼（含具體產出物）。當使用者要 A、B、C 時使用。`
把你自己口語會講的詞都塞進去（雞蛋糕、刀療、批量、n8n…）。

## 四、檔案怎麼分

```
你的skill/
├── SKILL.md       ← 流程與規則。控制在 500 行內
├── references/    ← 長資料：品牌設定、範本庫、案例、價目表
├── scripts/       ← 程式能算的就別讓 AI 猜：字數、格式、驗證
└── assets/        ← 圖片、字型、模板檔
```

**為什麼要分？** `SKILL.md` 被觸發時整份載入，`references/` 只有真的用到才讀。
全部塞在 SKILL.md = 每次都燒你的額度。

`scripts/` 的價值最容易被低估：叫模型「數字數」「檢查有沒有違禁字」會出錯，
寫 20 行 Python 就 100% 準。範例見 `alien-post/scripts/check_post.py`。

## 五、怎麼測

1. 重開一個 Claude Code session（skill 在啟動時掃描）
2. 用**自然口氣**講一句真實需求，不要點名 skill：
   「幫我寫三篇 IG 貼文推刀療」
3. 看它有沒有自動載入。沒載入 → 回去改 `description`，不是改主文
4. 也可以直接點名測內容：`/alien-post`

## 六、懶人路線

不想自己寫，直接叫 Claude：

```
用 skill-creator 幫我做一個 skill，功能是 ___
```

`skill-creator` 會問你幾題然後把整包生出來。
但**還是要自己讀過一遍** —— 它不知道你的違禁字、你的價目、你的語氣。

---

## 常見雷

| 症狀 | 原因 |
|---|---|
| Skill 從來不被觸發 | `description` 太抽象，或沒寫「何時使用」 |
| 啟動報錯 | `name` 跟資料夾名不一致，或 frontmatter 沒在第一行 |
| 回應變慢、額度燒很快 | 什麼都塞進 SKILL.md，該搬去 `references/` |
| 輸出格式每次都不一樣 | 沒在 SKILL.md 寫死輸出格式範本 |
