# AmazingTalker Voice Reminder 診斷紀錄

本文件適用於 Blueprint v0.5.0。診斷系統的目標是讓一次 automation execution 的 calendar query、refresh、verification、TTS 與播放器流程能由同一個 `run_id` 重建，同時避免私人 Calendar URL 與 credentials 進入 log。

## 啟用與收集

1. 到 Home Assistant「設定 → 自動化與場景」。
2. 開啟由 AmazingTalker Voice Reminder Blueprint 建立的 automation。
3. 展開「診斷紀錄與除錯」。
4. 開啟「啟用診斷紀錄」。
5. 一般使用選 `normal`；重現問題時暫時選 `debug`。
6. 隱私模式優先保持 `safe`。
7. 重現一次問題。
8. 到「設定 → 系統 → 紀錄」開啟 full raw log，搜尋下列 logger：

   ```text
   blueprints.weihaochiu.amazingtalker_voice_reminder
   ```

9. 找到問題時間附近的 `run_id`，收集同一 ID 的所有行。
10. 完成後關閉診斷紀錄，或至少從 `debug` 改回 `normal`。

Home Assistant 的 condensed log 主要保留近期 warning/error；一般 diagnostic event 使用 `info`，因此請查看 full raw log。Automation trace 仍可同時使用；Home Assistant 預設只儲存最近 5 次 trace，可在 automation 設定調整 `trace.stored_traces`。

## Normal 與 Debug

`normal` 只記真正有動作或結果的流程，例如 scheduled refresh、morning summary、課前 refresh、reminder candidate、最後 verification、TTS、逐台播放器 dispatch 與音量恢復。

`debug` 另記有 cached event 時的 query window、可用 calendar 數量、事件數、query horizon 與可觀察 player state。

不論層級，沒有 cached event、refresh、candidate、warning 或 error 的一般一分鐘 heartbeat 完全不寫 diagnostic event。啟用 debug 不會產生每分鐘 `heartbeat OK`。

## Safe 與 Detailed

`safe` 可包含：

- Blueprint version、run ID、trigger、timezone 與 policy hint。
- Calendar、TTS、player entity ID。
- Query start/end、event count、remaining minutes。
- `last_reported` 前後值、refresh/verification result。
- Player initial/observed state、initial/target/observed volume。
- TTS language、message length、player count 與 announce flag。

`safe` 不包含學員播報名稱、event summary 或完整 TTS message。

`detailed` 可額外包含學員播報名稱與 event summary。它仍不會記錄完整 TTS message。

兩種模式都永遠禁止：

- AmazingTalker private Calendar URL。
- Home Assistant URL 或 access token。
- Authorization header、cookie、password、API key 或其他 credentials。
- 含 credentials/query token 的完整 API URL。
- Remote Calendar integration config 或整個 state object。

Blueprint 的 diagnostic templates 只組合明確 allowlist 欄位；它不讀取 Remote Calendar URL，也不把 learner input、event object、state object 或 action payload 整包送入 logger。

## 結構與結果語意

每行是單一 JSON object，固定基本欄位如下：

```json
{"timestamp":"2026-08-21T18:30:00+08:00","version":"v0.5.0","run_id":"20260821T183000000000-heartbeat","trigger":"heartbeat","level":"normal","event":"REMINDER_CANDIDATE","result":"candidate"}
```

- `timestamp`：事件寫入時間。
- `version`：Blueprint version。
- `run_id`：同次 execution 的 correlation ID。
- `trigger`：`heartbeat`、`morning_summary` 或安全 fallback。
- `level`：事件層級 `normal` 或 `debug`。
- `event`：固定 event code。
- `result`：事件結果。

`action_dispatched` 只代表 Home Assistant 已派送 action。`media_player.volume_set` 與 `media_player.play_media` 沒有通用的成功 response，所以 Blueprint 不會把「後續 action 繼續執行」寫成 `success`。Calendar refresh 則以可觀察的 `last_reported` 前進判定 `completed`；沒有前進時為 `failed`，reason 為 `last_reported_not_advanced` 或 `calendar_unavailable`。

## Event codes

| Event | 意義 |
| --- | --- |
| `AUTOMATION_START` | 一次有意義的 diagnostic flow 開始及環境 header。 |
| `SCHEDULED_REFRESH_START` | 定期強制更新開始。 |
| `SCHEDULED_REFRESH_RESULT` | 定期更新 action 已派送及 calendar 計數。 |
| `MORNING_QUERY_START` | 早晨本地日界線 query 開始。 |
| `MORNING_QUERY_RESULT` | 早晨 query event count 或無可用 calendar。 |
| `MORNING_SUMMARY_CREATED` | 已建立非空早晨 TTS message。 |
| `MORNING_SUMMARY_SKIPPED` | 無 timed event 或無可用 calendar。 |
| `HEARTBEAT_ACTIONABLE` | Heartbeat 有 cached event、refresh 或 reminder work。 |
| `CALENDAR_QUERY_START` | Debug：heartbeat cache query window。 |
| `CALENDAR_QUERY_RESULT` | Debug：heartbeat query event count。 |
| `REFRESH_REQUIRED` | Cached event 到達 pre-class refresh 點。 |
| `CALENDAR_REFRESH_START` | 指定 calendar refresh 前 snapshot。 |
| `CALENDAR_REFRESH_RESULT` | 依 `last_reported` 判斷完成或失敗。 |
| `REMINDER_CANDIDATE` | Event 符合設定的 reminder offset。 |
| `REMINDER_VERIFY_START` | 最後確認前 refresh 開始。 |
| `REMINDER_VERIFY_RESULT` | Candidate 確認或 fail-closed 原因。 |
| `REMINDER_CONFIRMED` | Candidate 可進入 TTS message。 |
| `REMINDER_SKIPPED` | Candidate 因 refresh、unavailable、取消或改期而跳過。 |
| `TTS_PREPARE` | TTS entity、語言、長度、player count 與 announce 設定。 |
| `PLAYER_VOLUME_SET` | 播報音量 action 派送及可觀察 volume。 |
| `PLAYER_PLAY_START` | 單台播放器播放前狀態。 |
| `PLAYER_PLAY_RESULT` | 播放 action 派送，或 unavailable 而跳過。 |
| `PLAYER_VOLUME_RESTORE` | 單台恢復開始，或因沒有 volume 而跳過。 |
| `PLAYER_VOLUME_RESTORE_RESULT` | 恢復 action 派送或 `restore_skipped`。 |
| `AUTOMATION_COMPLETE` | 有意義 flow 結束。 |
| `WARNING` | 保留的 warning 類別。 |
| `ERROR` | 保留的 error 類別。 |

常見 `REMINDER_SKIPPED` reason：

- `calendar_refresh_failed`
- `calendar_unavailable`
- `event_missing_after_refresh`
- `event_identity_changed`

## Retention 與實體檔案限制

`diagnostic_log_retention_days` 預設為 7，可選 1～30。這個值只寫入 `AUTOMATION_START.retention_days_hint`，供使用者、外部 log collector 或未來 companion tooling 參考。它不會改變任何 Home Assistant retention。

目前沒有真正的自動 N-day retention，原因如下：

- Automation Blueprint 沒有任意 filesystem API，不能自行建立 `/config/amazingtalker_logs/amazingtalker-YYYY-MM-DD.jsonl`。
- 官方 File integration 可透過 `notify.send_message` append 到使用者預先建立的固定檔案；目錄需先存在並加入 `allowlist_external_dirs`。它不提供 Blueprint 可呼叫的動態每日檔名或 N-day cleanup action。
- Recorder 的 `purge_keep_days` 管理 Recorder database，不管理 `home-assistant.log` 或 File notification 文字檔。
- `shell_command` 必須由使用者在全域設定明確建立，HAOS 中在 Home Assistant container 內執行、工具有限且有 timeout。由可攜 Blueprint 帶入刪檔命令不安全，也無法自動安裝。

因此 v0.5.0 只使用不需額外依賴的 `system_log.write`。Home Assistant 的 raw system-log rotation、備份與刪除由安裝環境管理。若使用者另建 File integration 或外部 collector，必須在外部獨立設定 rotation/cleanup；Blueprint 不會宣稱已套用 7 天。

## 分享給 ChatGPT 或 Codex

建議只提供：

- 問題時間與 Home Assistant version。
- 相同 `run_id` 的完整 diagnostic lines。
- 使用的 TTS/player integration 種類（不需家庭 entity ID 時可再匿名化）。
- 預期行為與實際行為。

Safe mode 可直接用於支援，但仍建議快速搜尋 `http://`、`https://`、`token`、`authorization`、`cookie` 與私人姓名。Detailed mode 必須人工確認學員名稱與 summary 是否可分享。

假資料範例見 [diagnostic-log-example.jsonl](examples/diagnostic-log-example.jsonl)。

## 官方技術依據

- [System Log](https://www.home-assistant.io/integrations/system_log/)
- [Testing and troubleshooting automations](https://www.home-assistant.io/docs/automation/troubleshooting/)
- [Blueprint selectors](https://www.home-assistant.io/docs/blueprint/selectors/)
- [File integration](https://www.home-assistant.io/integrations/file)
- [Recorder](https://www.home-assistant.io/integrations/recorder)
- [Shell Command](https://www.home-assistant.io/integrations/shell_command)
