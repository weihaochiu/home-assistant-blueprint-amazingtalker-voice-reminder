# AmazingTalker 多學員課程語音提醒

[English](README.md)

**目前 Blueprint 版本：v0.5.0**

**最低 Home Assistant：2026.1.0**

[![開啟 Home Assistant 並匯入此 Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fweihaochiu%2Fhome-assistant-blueprint-amazingtalker-voice-reminder%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fweihaochiu%2Famazingtalker_voice_reminder.yaml)

這是 Home Assistant Automation Blueprint，可將任意數量學員的 AmazingTalker 行事曆合併成自然繁體中文早晨摘要與課前語音提醒。本專案是獨立社群作品，並非 AmazingTalker 官方專案，亦未獲 AmazingTalker 授權、背書或維護。

## 功能

- 使用可重複 object selector 新增任意數量學員。
- 每分鐘只讀 Remote Calendar coordinator 快取，不會每分鐘下載 AmazingTalker Calendar URL。
- 每日、每週、每月額外強制更新與月底 fallback。
- 一次播報當天所有非全天課程，支援一位學員多堂課。
- 早晨 5 種開場與課前 5 種提醒語句可複選。
- 選 1 個固定播放；選 2 個以上則每次實際播報純 random 一個。
- 任意段課前提醒、課前重新同步及每段播放前 fail-closed 最後確認。
- 優先以 ICS UID 確認；沒有 UID 時使用 calendar/start/end/summary。
- 合併同時間課程及同一檢查時間的不同剩餘分鐘。
- 多播放器錯誤隔離、分別恢復原音量、選擇性 Announcement 媒體恢復。
- 可選、隱私安全的結構化診斷紀錄；同次有效執行共用 run ID，空白分鐘 heartbeat 完全不寫 log。

## 系統需求

- Home Assistant 2026.1.0 以上。條件式排程表單使用的 choose selector 於 Home Assistant 2026.1 引入。
- 每位學員各一個 Remote Calendar；至少一個 `media_player` 與一個 `tts` 實體。
- 第一個正式驗證目標為 Google Translate TTS、HomePod Mini 與 `media_player.play_media`。
- 播放器需能存取 Home Assistant 產生的 TTS；若無聲音，檢查「設定 → 系統 → 網路」本機 URL。
- 不使用 HACS，不含 `custom_components`，也不建立 `hacs.json`。

## 第一次設定 AmazingTalker 行事曆

Blueprint 只會讀取 Home Assistant 已建立的 `calendar.*` 實體。第一次使用時，請從 AmazingTalker 取得私人 Calendar URL，再由 Home Assistant 的 Remote Calendar 建立實體：

```text
AmazingTalker
        ↓
Account Settings
        ↓
Connect to Calendar
        ↓
Copy URL
        ↓
Home Assistant
        ↓
Settings
        ↓
Devices & services
        ↓
Add Integration
        ↓
Remote Calendar
        ↓
Calendar Name / Calendar URL / Verify SSL certificate
        ↓
Submit / Finish
        ↓
calendar.*
        ↓
Calendar Dashboard 確認課程
        ↓
AmazingTalker Voice Reminder Blueprint
```

以下步驟依據 [AmazingTalker 官方 Calendar 說明](https://amazingtalker.elevio.help/en/articles/248-how-do-i-connect-with-my-online-calendar) 與 [Home Assistant 官方 Remote Calendar 說明](https://www.home-assistant.io/integrations/remote_calendar/)。

### 步驟 1：取得 AmazingTalker Calendar URL

1. 使用瀏覽器登入 AmazingTalker。
2. 開啟自己的 **Account Settings（帳號設定）**。
3. 在設定頁向下找到 **Connect to Calendar**。
4. 找到 AmazingTalker 提供的 Calendar subscription URL。
5. 按下 **Copy URL**。
6. AmazingTalker Calendar URL 會複製到剪貼簿。

**Copy URL 得到的是 AmazingTalker Calendar 的私人訂閱網址。**它不是 Home Assistant URL，也不是下載後的 Calendar 檔案。後續只要把完整網址直接貼入 Remote Calendar：不需要下載 `.ics`、不需要自行在瀏覽器打開網址、不需要 Developer Tools，也不需要從 Network request 尋找 API。

> **⚠️ AmazingTalker Calendar URL 是私人讀取網址**
>
> 這個網址可讀取私人課程資料，請視同密碼保管。不要 commit 到 Git、不要貼到 GitHub Issue、論壇、公開聊天或 README，也不要讓完整網址出現在螢幕截圖中。文件或求助時只能使用下列假資料：
>
> `https://api.amazingtalker.com/v1/user/calendar/REPLACE_WITH_YOUR_PRIVATE_TOKEN`

### 步驟 2：在 Home Assistant 新增 Remote Calendar

1. 開啟 Home Assistant。
2. 進入 **設定（Settings）**。
3. 選擇 **裝置與服務（Devices & services）**。
4. 點選右下角 **新增整合（Add Integration）**。
5. 搜尋 `Remote Calendar`。
6. 選擇 **Remote Calendar**。

這裡必須選 **Remote Calendar**，不要改用其他 Calendar integration。

### 步驟 3：填寫 Remote Calendar

依照 Home Assistant 畫面填寫：

| Home Assistant 欄位 | AmazingTalker 要填什麼 |
| --- | --- |
| **Calendar Name** | 自訂容易辨認的顯示名稱，例如 `AmazingTalker Grace`、`AmazingTalker Amy` 或 `AmazingTalker Kevin`。 |
| **Calendar URL** | 貼上 AmazingTalker **Copy URL** 複製的完整私人網址。 |
| **Verify SSL certificate** | 保持開啟；HTTPS 正常情況不應關閉憑證驗證。 |
| **Username** | 只有 URL 需要 HTTP Basic Authentication 時才會在額外步驟出現；AmazingTalker URL 一般不需要。 |
| **Password** | 同上；不要填入 AmazingTalker 登入密碼。 |

Calendar Name 只是 Home Assistant 的自訂顯示名稱，不保證最後的 entity ID 與它完全相同。

在 **Calendar URL** 欄位，將剛才從 **AmazingTalker → Account Settings → Connect to Calendar → Copy URL** 複製的完整網址直接貼上。不要移除尾端 token、不要手動補 `.ics`、不要只貼一部分，也不要貼成 AmazingTalker 首頁網址。文件中的安全格式只能是：

```text
https://api.amazingtalker.com/v1/user/calendar/REPLACE_WITH_YOUR_PRIVATE_TOKEN
```

Remote Calendar 支援 HTTP Basic Authentication，但 AmazingTalker 的私人 Calendar URL 一般不需要額外帳密。若 Home Assistant 沒有顯示 Username / Password 畫面是正常的；請勿把 AmazingTalker 登入 Email 或 Password 填入 Remote Calendar。

確認資料後按畫面上的 **Submit / Finish（提交／完成）**。若連線失敗，先確認 Calendar URL 是否完整；不要把關閉 SSL verification 當作一般疑難排解方式。

### 步驟 4：確認 calendar entity

1. 完成 Remote Calendar 設定。
2. 回到 **設定（Settings）→ 裝置與服務（Devices & services）**。
3. 開啟 **Remote Calendar** integration。
4. 找到剛建立的 Calendar entity。
5. 確認實際 entity ID 以 `calendar.` 開頭，例如 `calendar.amazingtalker_grace`。
6. 開啟 Home Assistant 的 **行事曆（Calendar）** dashboard，勾選剛建立的行事曆，確認近期 AmazingTalker 課程有顯示。

Remote Calendar 是唯讀整合，不會修改 AmazingTalker 課程。Entity ID 可能因 Calendar Name 與既有實體而不同，請以自己的 Home Assistant 實際顯示值為準。

> **Calendar Dashboard 看不到課程時，先不要檢查 Blueprint。**
>
> 這代表問題仍在 AmazingTalker Calendar URL 或 Remote Calendar 層。先讓課程正確出現在 Calendar dashboard，再繼續設定 Blueprint。

### 步驟 5：把 AmazingTalker Calendar 加入 Blueprint

1. 使用本頁上方按鈕匯入 **AmazingTalker Voice Reminder Blueprint**。
2. 建立 Automation。
3. 展開 **學員行事曆**。
4. 在 **學員** 欄位新增一筆。
5. **AmazingTalker 行事曆**選擇步驟 4 建立的 `calendar.*` entity。
6. **TTS 播報名稱（選填）**可以留白，也可以輸入希望 TTS 念出的名稱。
7. 選擇至少一個播放器與一個 TTS 實體，完成其他設定後儲存並啟用 automation。

單一學員範例：

```text
AmazingTalker 行事曆
calendar.amazingtalker_grace

TTS 播報名稱
Grace
```

多位學員使用不同 Calendar URL 時，每個 URL 各建立一個 Remote Calendar，再分別加入 Blueprint：

```text
Grace AmazingTalker URL
        ↓
Remote Calendar
        ↓
calendar.amazingtalker_grace

Amy AmazingTalker URL
        ↓
Remote Calendar
        ↓
calendar.amazingtalker_amy

Blueprint 學員 1
Calendar = calendar.amazingtalker_grace
播報名稱 = Grace

Blueprint 學員 2
Calendar = calendar.amazingtalker_amy
播報名稱 = Amy
```

### 步驟 6：第一次測試

依序確認：

1. Calendar dashboard 已看得到 AmazingTalker 課程。
2. Blueprint 選到相同的 `calendar.*` entity。
3. Automation 已啟用。
4. 選取的 `tts.*` entity 可用。
5. 選取的 `media_player.*` 可用。
6. 暫時把早晨摘要時間設成幾分鐘後，或使用適合的 reminder offset 進行實際測試。

**當天沒有非全天課程時，早晨摘要本來就不會播放，也不會調整音量。**這是正常的 no-course 行為，不代表 Blueprint 故障。

### Remote Calendar 更新方式

Remote Calendar integration 啟動時會抓取遠端資料；失敗時會重試，之後內建更新間隔為每 24 小時。Blueprint 的定期強制更新、課前重新同步與每段提醒前最後確認，會在需要時額外呼叫 `homeassistant.update_entity` 要求刷新。

每分鐘 heartbeat 正常只用 `calendar.get_events` 讀取 Remote Calendar coordinator cache，**不會每分鐘下載 AmazingTalker Calendar URL**。只有 scheduled refresh、pre-class refresh 與 reminder verification 會要求 `update_entity`。

### 第一次設定疑難排解

```text
AmazingTalker 有 Calendar URL？
        │
       Yes
        ↓
Remote Calendar 建立成功？
        │
       Yes
        ↓
calendar.* available？
        │
       Yes
        ↓
Calendar Dashboard 看得到課？
        │
       Yes
        ↓
Blueprint 選對 calendar.*？
        │
       Yes
        ↓
TTS / media_player 正常？
```

- **Calendar Dashboard 沒有課程：**問題仍在 Calendar URL／Remote Calendar 層，先不要檢查 Blueprint。
- **Calendar Dashboard 有課但沒有播報：**再檢查 Blueprint 選取的 entity、Automation 是否啟用、TTS、播放器、早晨時間或 reminder offset。

## TTS 設定

新增/啟用 TTS 整合，選擇其 `tts.*` 實體，保留 `zh-tw`（或使用該引擎支援語言），並選擇例如 `media_player.living_room_speaker` 的播放器。播放使用官方格式：

```text
media-source://tts/tts.example?message=<URL-ENCODED-MESSAGE>&language=zh-tw
```

此 URL 交給 `media_player.play_media`，搭配 `media_content_type: music` 與設定的 `announce`。沒有硬編碼 TTS 或播放器實體。

## 安裝 Blueprint

按上方按鈕，或在「設定 → 自動化與場景 → Blueprint → 匯入 Blueprint」貼上：

```text
https://github.com/weihaochiu/home-assistant-blueprint-amazingtalker-voice-reminder/blob/main/blueprints/automation/weihaochiu/amazingtalker_voice_reminder.yaml
```

匯入後建立 automation，至少新增一位學員、選一台播放器與一個 TTS 實體。

## 設定欄位

| Input | 預設 | 實際行為 |
| --- | --- | --- |
| `learners` | 必填 | 可重複新增；必填 `calendar_entity`、選填 `spoken_name`；至少一個有效 calendar。 |
| `media_players` | 必填 | 一個或多個播放器；錯誤逐台隔離。 |
| `tts_entity` | 必填 | TTS media-source 使用的 provider entity。 |
| `tts_language` | `zh-tw` | 傳給 TTS 的語言。 |
| `announcement_volume` | `0.8` | 暫時播報音量 0.0～1.0。 |
| `restore_original_volume` | `true` | 分別保存/恢復每台有回報的 `volume_level`。 |
| `attempt_media_resume` | `false` | 關閉為 `announce: false`；開啟為 `announce: true`。 |
| `enable_scheduled_update` | `true` | 額外強制更新排程。 |
| `update_frequency` | 每天 `07:00:00` | 結構化 choose selector 排程。每天只顯示時間；每週另顯示複選星期；每月另顯示複選日期。 |
| `enable_morning_summary` | `true` | 啟用早晨摘要。 |
| `morning_summary_time` | `07:12:00` | 關閉摘要時忽略。 |
| `morning_intro_styles` | `morning_standard` | 選 1 個固定；複選時每次實際早晨播報純 random 一次。 |
| `enable_pre_class_reminders` | `true` | 啟用 heartbeat 課前提醒。 |
| `pre_class_message_styles` | `preclass_standard` | 選 1 個固定；複選時每次實際課前播報純 random 一次。 |
| `reminder_offsets` | `30`、`10` | 任意段；執行時轉整數、去除無效/零/負數/重複並降冪排序，不改寫 UI。 |
| `enable_pre_class_refresh` | `true` | 到刷新點時只更新含課程的 calendar。 |
| `pre_class_refresh_minutes` | `60` | 課前重新同步分鐘數。 |
| `verify_before_each_reminder` | `true` | 每段播放前再更新確認；失敗跳過受影響提醒。 |
| `enable_diagnostic_logging` | `false` | 寫結構化 diagnostic events 到 Home Assistant system log；關閉時既有 warning 仍保留。 |
| `diagnostic_log_level` | `normal` | `normal` 只記有意義動作；`debug` 增加 query／計數／狀態，但空 heartbeat 仍不記。 |
| `diagnostic_log_retention_days` | `7` | 只作 metadata policy hint；Blueprint 無法控制 system log 或實體檔案 retention。 |
| `diagnostic_privacy_mode` | `safe` | `safe` 不含學員／summary；`detailed` 可含兩者，但所有模式都不記 URL 或憑證。 |

未來新增選填 input 時會提供 default，避免既有 automation 因缺少新欄位而無法載入。

## 每天／每週／每月更新規則

- **每天：**只顯示「更新時間」。例如每天 `07:00` 強制更新。
- **每週：**只顯示「更新時間」與可複選的「更新星期」。例如同時選星期一、星期三、星期五，代表每週一、三、五 `07:00` 更新。
- **每月：**只顯示「更新時間」與可複選的「更新日期」。例如同時選 1、15、30，代表每月 1、15、30 日 `07:00` 更新。
- 選 29、30、31 日但當月沒有該日，會 fallback 到該月最後一天；閏年二月為 29 日、平年二月為 28 日、小月為 30 日。
- 多個日期 fallback 到同一天時會先去重。例如 2026 年 2 月選 28、29、30、31，effective days 只有 `[28]`，2 月 28 日只更新一次。
- 每週或每月沒有任何有效選擇時採 fail-safe，不執行定期更新。

排程共用既有一分鐘 heartbeat，依 Home Assistant 本地 `HH:MM` 判斷，因此符合時間的一分鐘最多執行一次 scheduled refresh。定期更新與課前重新同步、reminder verification、課前提醒是獨立流程；同分鐘符合時仍會繼續執行兩者。

定期強制更新只會額外要求 Remote Calendar 更新，無法降低 Remote Calendar integration 自身的內建更新頻率。

### 從舊版排程升級

本版已移除舊的 `update_time`、`update_weekday`、`update_month_day` inputs 與 scalar 排程 runtime。依 Home Assistant 2026.1.0 官方 source，[Blueprint instance schema](https://github.com/home-assistant/core/blob/2026.1.0/homeassistant/components/blueprint/schemas.py) 允許 automation 中存在額外的已儲存 input key，而 [`BlueprintInputs`](https://github.com/home-assistant/core/blob/2026.1.0/homeassistant/components/blueprint/models.py) 只檢查新版 Blueprint 是否缺少必要 input；因此這三個 stale keys 會被忽略，不會單獨造成 automation 或 Blueprint 載入失敗。

舊 automation 內的 `update_frequency: daily`、`weekly` 或 `monthly` scalar 無法確認新版星期／日期選擇，所以本版會 fail-safe 停止**定期強制更新**，不會偷偷改成星期一、每天 07:00 或其他預設。若定期強制更新仍啟用且 scalar 尚未遷移，v0.5.0 會在本地時間 `00:00` 寫入 `system_log` migration warning，正常情況每天最多一次。早晨摘要、課前重新同步、提醒、verification 與 TTS 仍是獨立流程。

更新 Blueprint 後請：

1. 開啟既有 automation。
2. 展開「定期強制更新」。
3. 在「更新排程」重新選擇「每天／每週／每月」。
4. 重新設定時間，以及需要的星期或日期。
5. 儲存 automation。

不需要為 stale inputs 手動編輯 YAML；只要重新儲存結構化「更新排程」。

## 早晨提醒

在指定本地時間以 `calendar.get_events` 查詢當天本地 00:00 至隔日本地 00:00，忽略全天事件，依開始時間及學員排序並播報每位學員全部課程。名稱依序使用非空白 `spoken_name`、calendar `friendly_name`、移除 `calendar.` 的 entity ID。

時間會念成 `08:00` →「早上8點」、`13:30` →「下午1點30分」、`20:00` →「晚上8點」。沒有課程時，不設定音量、不播放 TTS。

「早晨開場語句」用原生 list-style 複選直接顯示 5 個完整句子，不再只顯示抽象名稱：

```text
☑ 早安提醒，今天有 AmazingTalker 課程。
☑ 早安，今天的 AmazingTalker 課程安排如下。
☐ 今天有 AmazingTalker 課程，以下是今天的課程時間。
☐ 新的一天開始了，今天的 AmazingTalker 課程安排如下。
☐ 早安，以下是今天的 AmazingTalker 課程時間。
```

上方勾選狀態只是操作示意。Home Assistant 會以原生 `select` selector 的 `multiple: true`、`mode: list` 呈現，不需 custom card 或 component。實際儲存值仍為 `morning_standard`、`morning_schedule`、`morning_today_courses`、`morning_new_day`、`morning_brief`，因此 v0.4.0 已儲存的選擇相容。

選 1 個時固定使用；選 2 個以上時，每次真正需要早晨 TTS 才純 random 一次，允許連續兩次抽到同一句。只有開場句會改變，後方學員與課程時間仍由 Calendar 動態產生。當天沒有 timed lesson 時，不抽語句、不調音量、不播放。

## 自訂提醒、重新同步與取消確認

「課前提醒語句」同樣直接顯示完整範例句：

```text
☑ 提醒您，Grace 的 AmazingTalker 課程將在30分鐘後開始。
☑ 記得準備教材，再過30分鐘，Grace 的 AmazingTalker 課程就要開始了。
☐ 課程提醒，Grace 的 AmazingTalker 課程再過30分鐘就要開始了。
☐ 準備上課囉，Grace 的 AmazingTalker 課程將在30分鐘後開始。
☐ 別忘了，30分鐘後有 Grace 的 AmazingTalker 課程。
```

`Grace` 與 `30分鐘` 只是 UI 範例。實際播報會自動代入所選 Calendar／帳號的 `spoken_name` 與真正剩餘分鐘數。實際儲存值仍為 `preclass_standard`、`preclass_material`、`preclass_coming`、`preclass_ready`、`preclass_short`，相容 v0.4.0 已儲存的選擇。

選 1 個時固定使用；選 2 個以上時，每次最後確認成功且真正需要播報時純 random 一次，允許連續抽到同一句。同一 playback 合併的所有 reminder offset 使用同一 style；`{names}` 與 `{minutes}` 仍由系統動態代入。

`names` 來自 `spoken_name`，用來區分 AmazingTalker Calendar／帳號。v0.5.0 不從 event summary 解析老師名稱；summary 仍保留於取消／改期確認所需的 fallback event identity。

Home Assistant 無法從任意長度 input 動態產生 calendar triggers，因此使用每分鐘 heartbeat。每次開始保存 `check_time` 與固定比較分鐘；舊 parallel 執行不會延遲後改用新的 `now()`。

每分鐘 `calendar.get_events` 只讀 coordinator 記憶體，不會無條件 `update_entity`。只有定期排程、課前刷新點與每段實際提醒前最後確認可強制更新；同一 heartbeat 的 calendar target 會去重。

最後確認優先比對 ICS `UID`；沒有 UID 時比對 calendar entity、start、end、summary。找不到視為取消；同 UID 但開始時間改變視為改期，舊時間不播。刷新失敗、`last_reported` 未前進、calendar unavailable 或重新查詢找不到事件時，fail-closed 跳過並安全嘗試寫 `system_log` warning。

Remote Calendar 內部保有 UID，但官方 `calendar.get_events` 目前不回傳 UID。Blueprint 保留未來 response 出現 UID 時的優先路徑；現行 Home Assistant 實際採 calendar/start/end/summary fallback。這是官方 action API 限制，不能宣稱目前已取得 UID。

正常 time-pattern 每 event/offset 一次，並在單次執行內去重。純 Blueprint 不建立儲存 helper，所以完全相同分鐘的人工/外部重複觸發無法跨 restart 持久去重。

## Automation mode

使用 `parallel`、上限 10。`single` 可能在 TTS 等待時漏掉下一分鐘；`queued` 可能晚到才執行過期工作。`parallel` 保留各執行固定時間並避免永久佇列，上限防止負載無界。

## 多播放器、音量與媒體恢復

每台可用播放器分別 snapshot。設定音量、播放、恢復皆有獨立錯誤處理；單台 unknown/unavailable/action 失敗不阻止其他台。不同品牌不保證同步。

音量恢復會依訊息長度等待最低播放時間，再給 buffering 最多 10 秒穩定時間，最後逐台恢復。播放器沒有通用可靠的「此 TTS 已結束」訊號，故為 best effort；沒有 `volume_level` 時安全跳過。

`attempt_media_resume` 與 `restore_original_volume` 彼此獨立，四種組合都支援。

> 此功能依播放器與整合支援程度而定，不保證能恢復原本歌曲、播放進度或佇列。Music Assistant 及支援 Announcement 的播放器成功率較高；HomePod 原生播放、Siri 或 iPhone 直接 AirPlay 的內容可能無法恢復。Blueprint 不從不完整 media attributes 猜測 Apple Music URL、佇列或進度。

## HomePod 與 Music Assistant 限制

- HomePod Mini 搭配 Apple TV 整合是實機目標，但不同來源的狀態變化須在真機確認。
- `announce: true` 只是要求；不支援 Announcement 時可能能播 TTS 但不能恢復媒體。
- Music Assistant Announcement 通常較可靠，仍取決於 provider/player。
- 多品牌播放器開始與結束可能不同步。

## 診斷紀錄

診斷預設關閉。發生問題時，到「**設定 → 自動化與場景**」開啟由本 Blueprint 建立的 automation，展開「**診斷紀錄與除錯**」，啟用 logging、選 `debug`、重現一次問題，完成後再關閉或改回 `normal`。

每筆紀錄是 Home Assistant raw system log 中的一行 JSON，logger 固定為 `blueprints.weihaochiu.amazingtalker_voice_reminder`。`20260821T183000000000-heartbeat` 形式的 run ID 可串起同次 scheduled refresh、快取 query、指定刷新、verification、TTS、逐台播放與音量恢復。官方 action 沒有 success response 時只記 `action_dispatched` 或 `unknown`；程式繼續執行不會被當成成功證據。

`safe` 只含 entity ID、計數、時間、剩餘分鐘、可觀察 refresh/player state 與結果，不含學員名稱或 event summary。`detailed` 可增加這兩項，但仍永遠不會序列化 Remote Calendar URL、token、authorization、cookie、password 或 integration config。兩種模式都不記完整 TTS 文字。

到「**設定 → 系統 → 紀錄**」查看 full raw log，搜尋固定 logger 或 run ID；condensed view 主要只保留近期 warning/error。Safe mode 的設計可直接交給 ChatGPT/Codex 分析，但分享前仍建議人工快速確認；Detailed mode 分享前必須人工檢查。

`diagnostic_log_retention_days` 只會寫在 flow header 當 policy hint，**不會**真的 rotate 或刪除 log。純 Blueprint 沒有 filesystem API；File integration 指向使用者預先建立的固定檔案；Recorder retention 管理資料庫而非文字 log；通用 Blueprint 也不能安全安裝 `shell_command`。完整 event code、取得方式、隱私規則與 retention 邊界見 [診斷紀錄說明](docs/DIAGNOSTIC_LOGGING.md)。

## 隱私與安全

- AmazingTalker Calendar URL 視同密碼。
- 不公開 Home Assistant URL/access token、私人網路位址、家庭 entity ID、學員姓名或未遮蔽 trace。
- 文件/測試只用 `calendar.amazingtalker_student_1`、`media_player.living_room_speaker` 等假資料。
- 貢獻前執行隱私測試並人工檢查 `git diff`。

## 疑難排解

- **沒有 calendar entity：** 先建立 Remote Calendar。
- **沒有課程：** 檢查 Calendar dashboard、手動更新，並確認不是全天事件。
- **沒有聲音：** 檢查 TTS entity/語言與本機 URL 可達性。
- **提醒跳過：** 查看 trace 的刷新 timeout、unavailable、取消/改期或沒有播放器條件。
- **音量不準：** 播放器可能缺 `volume_level`、播放超過等待上限或狀態不可靠。
- **媒體不恢復：** 若整合不正確支援 Announcement，關閉 `attempt_media_resume`。
- **新課未發現：** 等待或強制 calendar 更新，並見已知限制。
- **收集診斷：** 開啟 `debug`、重現一次、依 run ID 搜尋 raw system log，完成後關閉 debug。

## 測試方法

```shell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m yamllint .
.venv/Scripts/python -m pytest -q
git diff --check
```

Linux/macOS 用 `.venv/bin/python`。實機步驟見 [docs/MANUAL_TEST_CHECKLIST.zh-TW.md](docs/MANUAL_TEST_CHECKLIST.zh-TW.md)。GitHub Actions 重跑 YAML、Blueprint/Jinja 靜態、邏輯、隱私、UTF-8、whitespace。只有真的在支援的 Home Assistant/container 執行後才宣稱 runtime configuration check。

## 更新 Blueprint

到「設定 → 自動化與場景 → Blueprint」，開啟選單並選「重新匯入 Blueprint」。重匯後，使用舊 scalar 排程的 automation 請依「從舊版排程升級」重新選擇結構化排程。

本 Blueprint 目前不會自動檢查或自動安裝更新。畫面中的版本號只代表 Home Assistant 目前載入的 Blueprint 版本；更新仍需由使用者手動執行「重新匯入 Blueprint」。

### 如何確認 Blueprint 是否已更新

重新匯入後開啟 automation 編輯頁，確認同時看得到：

- Blueprint 標題：`AmazingTalker 多學員課程語音提醒 · v0.5.0`
- 第一個 section description：`目前 Blueprint：v0.5.0`

若仍顯示舊版，請到「設定（Settings）→ 自動化與場景（Automations & scenes）→ Blueprint」，開啟 AmazingTalker Blueprint 的三點選單，選擇「重新匯入 Blueprint（Re-import blueprint）」，再重新開啟 automation。這是 Home Assistant 官方文件列出的社群 Blueprint 更新方式。

## 已知限制

- 早上快取存在、之後取消的課程，可在成功課前刷新/最後確認後停止提醒。
- 完全新增加且舊快取不存在的課程，仍依靠內建輪詢或定期強制更新發現。
- 官方 `calendar.get_events` 目前不公開 Remote Calendar UID，所以現行確認使用 calendar/start/end/summary；只有未來欄位可用時才會啟用 UID 比對。
- 課程改到更早且刷新時已錯過提醒點，不補發過去提醒。
- 純 Blueprint 沒有持久 event ledger，無法防止完全同分鐘外部重複觸發。
- TTS 結束、音量/媒體恢復與 HomePod 行為皆為播放器相關 best effort。
- `diagnostic_log_retention_days` 只是 metadata hint；Blueprint 無法建立每日檔案或執行 N-day cleanup。
- Home Assistant system log rotation 與任何 File notification retention 均由安裝環境管理。
- 最終 runtime 仍需在使用者真實 Home Assistant、TTS、calendar 與播放器驗證。

## 官方技術依據

只依據官方來源：[AmazingTalker Calendar 說明](https://amazingtalker.elevio.help/en/articles/248-how-do-i-connect-with-my-online-calendar)、[Blueprint schema](https://www.home-assistant.io/docs/blueprint/schema/)、[selectors](https://www.home-assistant.io/docs/blueprint/selectors/)、[Remote Calendar](https://www.home-assistant.io/integrations/remote_calendar/)、[`calendar.get_events`](https://www.home-assistant.io/actions/calendar.get_events/)、[TTS](https://www.home-assistant.io/integrations/tts)、[`media_player.play_media`](https://www.home-assistant.io/actions/media_player.play_media/)、[System Log](https://www.home-assistant.io/integrations/system_log/)、[Automation trace](https://www.home-assistant.io/docs/automation/troubleshooting/)、[File](https://www.home-assistant.io/integrations/file)、[Recorder](https://www.home-assistant.io/integrations/recorder)、[Shell Command](https://www.home-assistant.io/integrations/shell_command) 與 [Music Assistant announcements](https://www.music-assistant.io/faq/announcement/)。

## 版本與 License

目前 Blueprint 版本：`v0.5.0`，見 [CHANGELOG.md](CHANGELOG.md)。[MIT](LICENSE) © 2026 weihaochiu。
