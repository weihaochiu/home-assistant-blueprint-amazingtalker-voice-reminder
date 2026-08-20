# AmazingTalker 課程語音提醒實機測試清單

用於真實 Home Assistant、Google Translate TTS、HomePod Mini、Music Assistant 及其他播放器。不可把真實 AmazingTalker Calendar URL、學員姓名、家庭 entity ID、Home Assistant URL、IP 或 access token 放到 Issue、截圖或公開紀錄。

## 測試前準備

- [ ] Home Assistant 2026.1.0 以上，且已備份 automation。
- [ ] 已建立測試 TTS；第一輪使用 Google Translate TTS。
- [ ] 已選至少一台播放器；HomePod Mini 先確認 Apple TV 整合可播放一般媒體。
- [ ] 「設定 → 系統 → 網路」本機 URL 可由播放器存取。

## 建立測試 Remote Calendar

1. 登入 AmazingTalker，開啟 **Account Settings → Connect to Calendar → Copy URL**。
2. 到 Home Assistant「設定 → 裝置與服務 → 新增整合」。
3. 新增 `Remote Calendar`，貼上測試專用 AmazingTalker Calendar 私人 URL，保持 SSL verification 開啟。
4. AmazingTalker URL 一般不需要 Username / Password；不可填入 AmazingTalker 登入帳密。
5. 每位測試學員各建一筆，在 Calendar dashboard 確認事件已載入。
6. Calendar URL 是私人讀取網址；測試後仍不可提交到 Git、Issue、公開論壇或未遮蔽截圖。

- [ ] 已由 AmazingTalker **Copy URL** 取得 Calendar URL。
- [ ] Remote Calendar 建立成功。
- [ ] 已建立可用的 `calendar.*` entity。
- [ ] Calendar dashboard 可看到近期課程。
- [ ] Blueprint 的「AmazingTalker 行事曆」可選到該 `calendar.*` entity。
- [ ] 實際 TTS 可由選定的播放器播放。

## 建立暫時測試課程

- [ ] 事件安排在至少 90 分鐘後，讓 Remote Calendar 更新與 automation reload 完成。
- [ ] 兩位學員同時間開始；同一學員同日兩堂；另建一個全天事件。
- [ ] 手動執行一次 `homeassistant.update_entity`，再從 Calendar dashboard 確認載入。

AmazingTalker 若不能建立任意暫時課程，可使用受控私人測試 Calendar server；不可在公開 server 放真實姓名/token。

## 先用短時間驗證

第一輪可暫設 `pre_class_refresh_minutes: 6`、`reminder_offsets: 4, 2`，並把早晨/更新時間設在數分鐘後。仍須先把事件排在足夠未來並等待快取載入。完成後恢復 60／30／10 或正式值。

## 早晨摘要

- [ ] 有課時只播放一次合併訊息；同一學員多堂與多位同時課程全部念出。
- [ ] 全天事件未念出。
- [ ] `08:00`、`13:30`、`20:00` 是「早上8點」、「下午1點30分」、「晚上8點」。
- [ ] 完全無課時不改音量、不播放。
- [ ] 關閉 `enable_morning_summary` 後不執行。

## 60／30／10 分鐘與自訂提醒

- [ ] 建立至少 70 分鐘後課程，保持 refresh 60、offsets 30/10。
- [ ] 60 分鐘處只刷新相關 calendar，不播放。
- [ ] 30 與 10 分鐘各播放一次；取消後兩段都不得播放。
- [ ] 多學員同時開始合成一句。
- [ ] 同 heartbeat 一位剩 30、另一位剩 10 時只播放一次但有兩句。
- [ ] 第三段自訂 offset 正常；關閉提醒 checkbox 後完全不播放。

## 取消、改期與更新失敗

1. 建立未來課程並等待載入，再於課前刷新前取消。
2. 確認刷新點及原 30/10 分鐘點皆不播放。
3. 另把課程改到較晚，確認舊時間不播、新時間依新資料計算。
4. 模擬 ICS 無法連線或 calendar unavailable，確認 fail-closed 跳過而非用舊快取。
5. 若改到更早且已錯過提醒點，只記錄限制，不期待補發。

## Automation trace

- [ ] 每次 trace 的 `check_time` 固定。
- [ ] 普通 heartbeat 只有 `calendar.get_events`，沒有無條件 `update_entity`。
- [ ] 刷新 target 去重；成功時看到 `last_reported` 前後變化。
- [ ] 失敗時看到條件與提醒跳過，並檢查 system log warning。
- [ ] 無課/無播放器在改音量前安全結束。
- [ ] 分享 trace 前遮蔽私人資料。

## 音量恢復

- [ ] 兩台播放器先設不同音量，開啟恢復後各回原值。
- [ ] 不會在 `play_media` 剛回傳就立刻降音量。
- [ ] 單台 unavailable 時其他台仍播放/恢復。
- [ ] 關閉恢復時播報後保持 announcement volume。
- [ ] 沒有 `volume_level` 的播放器安全跳過。

## announce、媒體恢復及四種組合

- [ ] volume restore 關／media resume 關。
- [ ] volume restore 開／media resume 關。
- [ ] volume restore 關／media resume 開。
- [ ] volume restore 開／media resume 開。

先播非重要測試音訊再觸發 TTS。開啟 resume 只記錄整合實際結果，不宣稱歌曲、進度、佇列一定恢復。HomePod 原生、Siri、iPhone AirPlay、Apple Music 分別記錄，禁止從 attributes 猜測重播。

## 多播放器、HomePod 與 Music Assistant

- [ ] 一台、兩台、三台皆測；不要求跨品牌同步，但記錄差異。
- [ ] 單台 action 失敗不阻止其他台。
- [ ] Music Assistant player 測 `announce: true` resume。
- [ ] HomePod Mini 測 `announce: false/true`，記錄 playing/buffering/idle/paused 狀態順序。

## 定期更新與月底

- [ ] UI 不再出現「舊版排程相容設定」。
- [ ] 「定期強制更新」後下一個主要 section 直接是「當天早晨課程播報」。
- [ ] choose selector 在每天只顯示時間、每週只顯示時間與星期、每月只顯示時間與日期。
- [ ] 每天排程在設定的本地時間正常更新。
- [ ] 每週可同時選星期一、三、五，且只在選取日的正確本地時間更新。
- [ ] 每月可同時選 1、15、30，且只在選取日期的正確本地時間更新。
- [ ] 平年二月 29/30/31 fallback 到 28；閏年到 29；小月 31 到 30。
- [ ] 2026 年 2 月選 28、29、30、31 時，2/28 只更新一次。
- [ ] `enable_scheduled_update: false` 時不做定期更新，但課前刷新與 verification 仍正常。
- [ ] 定期更新與課前刷新同分鐘發生時，兩個流程都完成且 reminder 未漏播。
- [ ] 排程只額外刷新，不改變 Remote Calendar 內建輪詢。

## 清理

- [ ] 恢復正式 refresh/offset/早晨/更新時間。
- [ ] 刪除暫時課程與不用的 Remote Calendar。
- [ ] 撤銷/輪替測試 Calendar URL token。
- [ ] 刪除含私人資料的 trace、下載檔與未遮蔽截圖。
- [ ] 最後檢查 dashboard/trace 無殘留待觸發測試。

結果紀錄只保留 Home Assistant 版本、匿名化播放器整合/TTS、日期、pass/fail 與去識別備註。
