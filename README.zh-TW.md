# AmazingTalker 多學員課程語音提醒

[English](README.md)

[![開啟 Home Assistant 並匯入此 Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fweihaochiu%2Fhome-assistant-blueprint-amazingtalker-voice-reminder%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fweihaochiu%2Famazingtalker_voice_reminder.yaml)

這是 Home Assistant Automation Blueprint，可將任意數量學員的 AmazingTalker 行事曆合併成自然繁體中文早晨摘要與課前語音提醒。本專案是獨立社群作品，並非 AmazingTalker 官方專案，亦未獲 AmazingTalker 授權、背書或維護。

## 功能

- 使用可重複 object selector 新增任意數量學員。
- 每分鐘只讀 Remote Calendar coordinator 快取，不會每分鐘下載 ICS。
- 每日、每週、每月額外強制更新與月底 fallback。
- 一次播報當天所有非全天課程，支援一位學員多堂課。
- 任意段課前提醒、課前重新同步及每段播放前 fail-closed 最後確認。
- 優先以 ICS UID 確認；沒有 UID 時使用 calendar/start/end/summary。
- 合併同時間課程及同一檢查時間的不同剩餘分鐘。
- 多播放器錯誤隔離、分別恢復原音量、選擇性 Announcement 媒體恢復。

## 系統需求

- Home Assistant 2026.1.0 以上。條件式排程表單使用的 choose selector 於 Home Assistant 2026.1 引入。
- 每位學員各一個 Remote Calendar；至少一個 `media_player` 與一個 `tts` 實體。
- 第一個正式驗證目標為 Google Translate TTS、HomePod Mini 與 `media_player.play_media`。
- 播放器需能存取 Home Assistant 產生的 TTS；若無聲音，檢查「設定 → 系統 → 網路」本機 URL。
- 不使用 HACS，不含 `custom_components`，也不建立 `hacs.json`。

## 建立 AmazingTalker Remote Calendar

Blueprint 不負責建立 Remote Calendar。

1. 到「設定 → 裝置與服務 → 新增整合」。
2. 新增 `Remote Calendar`。
3. 每位學員分別建立一筆，貼上該學員的 AmazingTalker ICS URL。
4. 不需要帳號及密碼；URL 本身包含私人讀取金鑰。
5. 完成後選擇產生的 `calendar.*` 實體，例如 `calendar.amazingtalker_student_1`。

> AmazingTalker ICS URL 是私人讀取金鑰，不可提交到 Git、貼到 GitHub Issue 或公開論壇。文件只能使用 `https://api.amazingtalker.com/v1/user/calendar/REPLACE_WITH_YOUR_PRIVATE_TOKEN` 這類假資料。

Remote Calendar 內建預設每 24 小時輪詢。Blueprint 排程是額外強制更新，無法降低 Remote Calendar 本身的內建更新頻率。

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
| `update_time` | `07:00:00` | 舊版相容值，只供既有 scalar 排程使用。 |
| `update_weekday` | `monday` | 舊版相容值，只供既有每週 scalar 排程使用。 |
| `update_month_day` | `1` | 舊版相容值，只供既有每月 scalar 排程使用。 |
| `enable_morning_summary` | `true` | 啟用早晨摘要。 |
| `morning_summary_time` | `07:12:00` | 關閉摘要時忽略。 |
| `enable_pre_class_reminders` | `true` | 啟用 heartbeat 課前提醒。 |
| `reminder_offsets` | `30`、`10` | 任意段；執行時轉整數、去除無效/零/負數/重複並降冪排序，不改寫 UI。 |
| `enable_pre_class_refresh` | `true` | 到刷新點時只更新含課程的 calendar。 |
| `pre_class_refresh_minutes` | `60` | 課前重新同步分鐘數。 |
| `verify_before_each_reminder` | `true` | 每段播放前再更新確認；失敗跳過受影響提醒。 |

Input key 會保持向後相容；未來新增選填 input 必有 default。

## 每天／每週／每月更新規則

- **每天：**只顯示「更新時間」。例如每天 `07:00` 強制更新。
- **每週：**只顯示「更新時間」與可複選的「更新星期」。例如同時選星期一、星期三、星期五，代表每週一、三、五 `07:00` 更新。
- **每月：**只顯示「更新時間」與可複選的「更新日期」。例如同時選 1、15、30，代表每月 1、15、30 日 `07:00` 更新。
- 選 29、30、31 日但當月沒有該日，會 fallback 到該月最後一天；閏年二月為 29 日、平年二月為 28 日、小月為 30 日。
- 多個日期 fallback 到同一天時會先去重。例如 2026 年 2 月選 28、29、30、31，effective days 只有 `[28]`，2 月 28 日只更新一次。
- 每週或每月沒有任何有效選擇時採 fail-safe，不執行定期更新。

排程共用既有一分鐘 heartbeat，依 Home Assistant 本地 `HH:MM` 判斷，因此符合時間的一分鐘最多執行一次 scheduled refresh。定期更新與課前重新同步、reminder verification、課前提醒是獨立流程；同分鐘符合時仍會繼續執行兩者。

定期強制更新只會額外要求 Remote Calendar 更新，無法降低 Remote Calendar integration 自身的內建更新頻率。

### 既有 automation 升級

`update_frequency` input ID 保持不變。既有 automation 若仍儲存舊版 `daily`、`weekly`、`monthly` scalar，會繼續使用原本的 `update_time`、`update_weekday`、`update_month_day`，不會默默換成不同排程。這些舊欄位收在預設折疊的「舊版排程相容設定」，新使用者只需使用條件式「更新排程」。升級後若開啟 automation 編輯器，請重新選擇一次「更新排程」以將表單值轉成新結構；在重新選擇以前，執行時仍保持舊排程。

## 早晨提醒

在指定本地時間以 `calendar.get_events` 查詢當天本地 00:00 至隔日本地 00:00，忽略全天事件，依開始時間及學員排序並播報每位學員全部課程。名稱依序使用非空白 `spoken_name`、calendar `friendly_name`、移除 `calendar.` 的 entity ID。

時間會念成 `08:00` →「早上8點」、`13:30` →「下午1點30分」、`20:00` →「晚上8點」。沒有課程時，不設定音量、不播放 TTS。

## 自訂提醒、重新同步與取消確認

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

## 隱私與安全

- ICS URL token 視同密碼。
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

到「設定 → 自動化與場景 → Blueprint」，開啟選單並選「重新匯入 Blueprint」。先看版本資訊；重匯會覆蓋 Blueprint，但保留相容 inputs。

## 已知限制

- 早上快取存在、之後取消的課程，可在成功課前刷新/最後確認後停止提醒。
- 完全新增加且舊快取不存在的課程，仍依靠內建輪詢或定期強制更新發現。
- 官方 `calendar.get_events` 目前不公開 Remote Calendar UID，所以現行確認使用 calendar/start/end/summary；只有未來欄位可用時才會啟用 UID 比對。
- 課程改到更早且刷新時已錯過提醒點，不補發過去提醒。
- 純 Blueprint 沒有持久 event ledger，無法防止完全同分鐘外部重複觸發。
- TTS 結束、音量/媒體恢復與 HomePod 行為皆為播放器相關 best effort。
- 最終 runtime 仍需在使用者真實 Home Assistant、TTS、calendar 與播放器驗證。

## 官方技術依據

只依據官方來源：[Blueprint schema](https://www.home-assistant.io/docs/blueprint/schema/)、[selectors](https://www.home-assistant.io/docs/blueprint/selectors/)、[Remote Calendar](https://www.home-assistant.io/integrations/remote_calendar/)、[`calendar.get_events`](https://www.home-assistant.io/actions/calendar.get_events/)、[TTS](https://www.home-assistant.io/integrations/tts)、[`media_player.play_media`](https://www.home-assistant.io/actions/media_player.play_media/) 與 [Music Assistant announcements](https://www.music-assistant.io/faq/announcement/)。

## 版本與 License

開發版本 `0.1.0`（Unreleased），見 [CHANGELOG.md](CHANGELOG.md)。[MIT](LICENSE) © 2026 weihaochiu。
