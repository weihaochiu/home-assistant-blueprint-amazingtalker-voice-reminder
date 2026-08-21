# AmazingTalker Multi-Learner Voice Reminder

[繁體中文](README.zh-TW.md)

**Current Blueprint version: v0.5.0**

**Minimum Home Assistant: 2026.1.0**

[![Open your Home Assistant instance and import this Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fweihaochiu%2Fhome-assistant-blueprint-amazingtalker-voice-reminder%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fweihaochiu%2Famazingtalker_voice_reminder.yaml)

A Home Assistant Automation Blueprint that combines any number of AmazingTalker learner calendars into natural Traditional Chinese morning summaries and pre-class voice reminders.

This is an independent community project. It is not an official AmazingTalker project and is not affiliated with or endorsed by AmazingTalker.

## Features

- Add any number of learners using the repeatable Home Assistant object selector.
- Read each Remote Calendar coordinator cache every minute without downloading the AmazingTalker Calendar URL every minute.
- Optional daily, weekly, or monthly forced refresh with end-of-month fallback.
- Morning summary covering every timed lesson for every learner; all-day events are ignored.
- Five selectable morning openings and five selectable pre-class reminder styles.
- One selected phrase stays fixed; multiple selections use pure random per actual playback.
- Any number of normalized pre-class reminder offsets, targeted refresh, and fail-closed final verification.
- Match by ICS UID, with calendar/start/end/summary fallback when UID is absent.
- Merge simultaneous lessons and different offsets into one playback request with natural sentences.
- Independent multi-player playback, per-player volume restoration, and optional announcement resume.
- Opt-in, privacy-safe structured diagnostics with one run ID across each meaningful execution; empty minute heartbeats stay silent.

## Requirements

- Home Assistant 2026.1.0 or newer. The choose selector used by the conditional schedule form was introduced in Home Assistant 2026.1.
- One Home Assistant Remote Calendar entry per learner.
- At least one `media_player` and one `tts` entity. Google Translate TTS is the first formal target.
- The player must be able to fetch TTS media from Home Assistant. Check **Settings → System → Network** if generated speech cannot play.
- HACS is not used. This repository contains no custom integration or `hacs.json`.

## First-time AmazingTalker calendar setup

The Blueprint reads an existing Home Assistant `calendar.*` entity. First copy the private Calendar URL from AmazingTalker, then use Home Assistant Remote Calendar to create that entity:

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
Confirm lessons in the Calendar dashboard
        ↓
AmazingTalker Voice Reminder Blueprint
```

These steps follow the official [AmazingTalker calendar instructions](https://amazingtalker.elevio.help/en/articles/248-how-do-i-connect-with-my-online-calendar) and [Home Assistant Remote Calendar documentation](https://www.home-assistant.io/integrations/remote_calendar/).

### Step 1: Get the AmazingTalker Calendar URL

1. Sign in to AmazingTalker in a browser.
2. Open your **Account Settings**.
3. Scroll down to **Connect to Calendar**.
4. Find the Calendar subscription URL supplied by AmazingTalker.
5. Select **Copy URL**.
6. The AmazingTalker Calendar URL is copied to your clipboard.

**Copy URL gives you the private subscription URL for your AmazingTalker Calendar.** It is not a Home Assistant URL or a downloaded calendar file. Paste the complete URL directly into Remote Calendar. Do not download an `.ics` file, open the URL yourself, use Developer Tools, or inspect network requests.

> **⚠️ The AmazingTalker Calendar URL is a private read URL**
>
> Treat it like a password because it can expose private lesson data. Do not commit it to Git or post it in a GitHub Issue, forum, public chat, README, or unredacted screenshot. Documentation and support requests must use this placeholder:
>
> `https://api.amazingtalker.com/v1/user/calendar/REPLACE_WITH_YOUR_PRIVATE_TOKEN`

### Step 2: Add Remote Calendar in Home Assistant

1. Open Home Assistant.
2. Open **Settings**.
3. Select **Devices & services**.
4. Select **Add Integration** in the bottom-right corner.
5. Search for `Remote Calendar`.
6. Select **Remote Calendar**.

Select **Remote Calendar** here rather than another calendar integration.

### Step 3: Complete the Remote Calendar form

Enter the following values:

| Home Assistant field | Value for AmazingTalker |
| --- | --- |
| **Calendar Name** | A recognizable display name such as `AmazingTalker Grace`, `AmazingTalker Amy`, or `AmazingTalker Kevin`. |
| **Calendar URL** | The complete private URL copied with AmazingTalker **Copy URL**. |
| **Verify SSL certificate** | Keep enabled; normal HTTPS setup should not disable certificate verification. |
| **Username** | Only appears in an additional step when the URL requires HTTP Basic Authentication; normally not needed for AmazingTalker. |
| **Password** | Same as above; never enter your AmazingTalker login password. |

Calendar Name is only a display name. It does not guarantee the exact entity ID that Home Assistant will create.

For **Calendar URL**, paste the complete value copied from **AmazingTalker → Account Settings → Connect to Calendar → Copy URL**. Do not remove the token at the end, add `.ics`, paste only part of the URL, or paste the AmazingTalker home page. Documentation must use only:

```text
https://api.amazingtalker.com/v1/user/calendar/REPLACE_WITH_YOUR_PRIVATE_TOKEN
```

Remote Calendar supports HTTP Basic Authentication, but an AmazingTalker private Calendar URL normally needs no additional credentials. It is normal if the UI never displays Username and Password. Never enter your AmazingTalker login email or password there.

Select **Submit / Finish**. If the connection fails, first verify that the Calendar URL is complete; disabling SSL verification is not a general troubleshooting step.

### Step 4: Confirm the calendar entity

1. Finish the Remote Calendar setup.
2. Return to **Settings → Devices & services**.
3. Open the **Remote Calendar** integration.
4. Find the Calendar entity you just created.
5. Confirm that its actual entity ID starts with `calendar.`, for example `calendar.amazingtalker_grace`.
6. Open Home Assistant's **Calendar** dashboard, select the calendar, and confirm that upcoming AmazingTalker lessons appear.

Remote Calendar is read-only and cannot modify lessons. The actual entity ID can vary with the Calendar Name and existing entities; always use the ID shown by your Home Assistant instance.

> **If the Calendar dashboard does not show lessons, do not troubleshoot the Blueprint yet.**
>
> The problem is still at the AmazingTalker Calendar URL or Remote Calendar layer. Make the lessons appear in the Calendar dashboard before continuing.

### Step 5: Add the learner to the Blueprint

1. Import the **AmazingTalker Voice Reminder Blueprint** with the button above.
2. Create an automation.
3. Expand **學員行事曆**.
4. Add an item to **學員**.
5. Under **AmazingTalker 行事曆**, select the `calendar.*` entity from Step 4.
6. Leave **TTS 播報名稱（選填）** blank or enter the name TTS should speak.
7. Select at least one media player and one TTS entity, then save and enable the automation.

Single-learner example:

```text
AmazingTalker 行事曆
calendar.amazingtalker_grace

TTS 播報名稱
Grace
```

For multiple private Calendar URLs, create one Remote Calendar entry for each URL and add each entity separately:

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

Blueprint learner 1
Calendar = calendar.amazingtalker_grace
Spoken name = Grace

Blueprint learner 2
Calendar = calendar.amazingtalker_amy
Spoken name = Amy
```

### Step 6: Run the first test

Check these items in order:

1. The Calendar dashboard shows an AmazingTalker lesson.
2. The Blueprint uses that same `calendar.*` entity.
3. The automation is enabled.
4. The selected `tts.*` entity is available.
5. The selected `media_player.*` is available.
6. Temporarily set the morning summary a few minutes ahead, or use a suitable reminder offset for a real test.

**The morning summary intentionally does not play when the local day has no timed lessons.** It also leaves player volume untouched; no speech in this case is not a Blueprint failure.

### Remote Calendar updates

Remote Calendar fetches remote data when the integration starts, retries after a failure, and then uses a built-in 24-hour update interval. The Blueprint's scheduled refresh, pre-class refresh, and final verification call `homeassistant.update_entity` when an additional refresh is needed.

The normal one-minute heartbeat only uses `calendar.get_events` to read the Remote Calendar coordinator cache. **It does not download the AmazingTalker Calendar URL every minute.** Only scheduled refresh, pre-class refresh, and reminder verification request `update_entity`.

### First-time setup troubleshooting

```text
AmazingTalker Calendar URL available?
        │
       Yes
        ↓
Remote Calendar created?
        │
       Yes
        ↓
calendar.* available?
        │
       Yes
        ↓
Lessons visible in Calendar dashboard?
        │
       Yes
        ↓
Correct calendar.* selected in Blueprint?
        │
       Yes
        ↓
TTS / media_player working?
```

- **No lessons in the Calendar dashboard:** the issue remains in the Calendar URL / Remote Calendar layer; do not troubleshoot the Blueprint yet.
- **Lessons appear but speech does not:** check the selected Blueprint entity, automation enabled state, TTS, player, morning time, and reminder offsets.

## Configure TTS

Add/enable a TTS integration, select its `tts.*` entity, keep `tts_language` as `zh-tw` (or use a supported language), and select players such as `media_player.living_room_speaker`. Playback uses the official media-source form:

```text
media-source://tts/tts.example?message=<URL-ENCODED-MESSAGE>&language=zh-tw
```

It is passed to `media_player.play_media` with `media_content_type: music` and the configured `announce` value. No TTS or player entity is hard-coded.

## Install

Use the button above, or import this URL under **Settings → Automations & scenes → Blueprints → Import Blueprint**:

```text
https://github.com/weihaochiu/home-assistant-blueprint-amazingtalker-voice-reminder/blob/main/blueprints/automation/weihaochiu/amazingtalker_voice_reminder.yaml
```

Then select **Create automation**, add at least one learner and player, choose a TTS entity, and save.

## Settings reference

| Input | Default | Behavior |
| --- | --- | --- |
| `learners` | Required | Repeatable objects with required `calendar_entity` and optional `spoken_name`; at least one valid calendar is required. |
| `media_players` | Required | One or more players; failures are isolated per player. |
| `tts_entity` | Required | TTS provider used in the media-source URL. |
| `tts_language` | `zh-tw` | Language sent to the TTS provider. |
| `announcement_volume` | `0.8` | Temporary volume from 0.0 to 1.0. |
| `restore_original_volume` | `true` | Save/restore each reported `volume_level` independently. |
| `attempt_media_resume` | `false` | `false` sends `announce: false`; `true` sends `announce: true`. |
| `enable_scheduled_update` | `true` | Enable the additional forced-refresh schedule. |
| `update_frequency` | Daily at `07:00:00` | Structured choose-selector schedule. Daily shows time only; weekly adds multiple weekdays; monthly adds multiple month days. |
| `enable_morning_summary` | `true` | Enable the local-day morning summary. |
| `morning_summary_time` | `07:12:00` | Ignored when morning summary is disabled. |
| `morning_intro_styles` | `morning_standard` | One opening stays fixed; multiple selected openings use pure random once per actual morning playback. |
| `enable_pre_class_reminders` | `true` | Enable heartbeat-based reminders. |
| `pre_class_message_styles` | `preclass_standard` | One style stays fixed; multiple selected styles use pure random once per actual reminder playback. |
| `reminder_offsets` | `30`, `10` | Repeatable minutes-before entries; runtime values become positive unique integers sorted descending without rewriting UI data. |
| `enable_pre_class_refresh` | `true` | Refresh only calendars whose cached lesson reaches the refresh point. |
| `pre_class_refresh_minutes` | `60` | Minutes before class for targeted refresh. |
| `verify_before_each_reminder` | `true` | Refresh and confirm immediately before playback; failure skips the affected reminder. |
| `enable_diagnostic_logging` | `false` | Write structured diagnostic events to the Home Assistant system log; existing warnings remain active while off. |
| `diagnostic_log_level` | `normal` | `normal` records meaningful actions; `debug` adds query/count/state details without empty-heartbeat noise. |
| `diagnostic_log_retention_days` | `7` | Metadata hint only; a Blueprint cannot control system-log or physical-file retention. |
| `diagnostic_privacy_mode` | `safe` | `safe` omits learner/summary; `detailed` may include them, but neither mode logs URLs or credentials. |

Future optional inputs will have defaults so existing automations do not fail because a new field is missing.

## Update schedule

- **Daily:** only the update time is shown. For example, `07:00` refreshes every day at 07:00.
- **Weekly:** the update time and a multiple-choice weekday field are shown. For example, Monday, Wednesday, and Friday at `07:00` refreshes on all three selected weekdays.
- **Monthly:** the update time and a multiple-choice day field are shown. For example, 1, 15, and 30 at `07:00` refreshes on all three selected dates.
- If a selected day 29, 30, or 31 does not exist, it falls back to that month's final day. Multiple selected dates that fall back to the same day are de-duplicated, so February receives one refresh for that minute.
- Empty weekly or monthly selections fail safe and do not run a scheduled refresh.

The existing one-minute heartbeat performs the scheduled check. It compares the local `HH:MM`, so the matching minute causes at most one scheduled refresh action. Scheduled refresh and pre-class refresh/reminder work remain independent within the same heartbeat.

The scheduled forced refresh only makes an additional Remote Calendar update request. It cannot reduce the Remote Calendar integration's own built-in polling interval.

### Upgrading an old schedule

This release removes the old `update_time`, `update_weekday`, and `update_month_day` inputs and scalar schedule runtime. The official Home Assistant 2026.1.0 [Blueprint instance schema](https://github.com/home-assistant/core/blob/2026.1.0/homeassistant/components/blueprint/schemas.py) permits extra stored input keys, while [`BlueprintInputs`](https://github.com/home-assistant/core/blob/2026.1.0/homeassistant/components/blueprint/models.py) only rejects missing inputs declared by the new Blueprint. Those three stale keys are therefore ignored and do not by themselves invalidate the automation or Blueprint.

An old `update_frequency: daily`, `weekly`, or `monthly` scalar cannot describe the new weekday or month-day selections. The runtime fails safe by disabling **scheduled refresh** until a structured schedule is saved; it does not silently choose Monday, daily at 07:00, or another default. While scheduled refresh is enabled and the scalar remains, v0.5.0 writes a migration warning to `system_log` at local `00:00`, normally at most once per day. Morning summaries, pre-class refresh, reminders, verification, and TTS remain independent.

After updating the Blueprint:

1. Open the existing automation.
2. Expand **定期強制更新**.
3. Reselect **每天**, **每週**, or **每月** under **更新排程**.
4. Set the time and any required weekdays or month days.
5. Save the automation.

There is no need to remove stale inputs by manually editing YAML; save the structured schedule in the automation editor.

## Morning summary

At the selected local time, `calendar.get_events` queries local 00:00 through the next local 00:00. Timed events are sorted by start and learner; all lessons are spoken. Name fallback is non-blank `spoken_name`, calendar `friendly_name`, then entity ID without `calendar.`. Times are natural: `08:00` → `早上8點`, `13:30` → `下午1點30分`, `20:00` → `晚上8點`. With no lessons, volume and TTS are untouched.

The native list-style multi-select shows complete built-in sentences instead of abstract style names:

```text
☑ 早安提醒，今天有 AmazingTalker 課程。
☑ 早安，今天的 AmazingTalker 課程安排如下。
☐ 今天有 AmazingTalker 課程，以下是今天的課程時間。
☐ 新的一天開始了，今天的 AmazingTalker 課程安排如下。
☐ 早安，以下是今天的 AmazingTalker 課程時間。
```

The check marks above illustrate a possible selection. Home Assistant renders this through its native `select` selector with `multiple: true` and `mode: list`; no custom card or component is required. Stored values remain `morning_standard`, `morning_schedule`, `morning_today_courses`, `morning_new_day`, and `morning_brief`, so v0.4.0 selections remain compatible.

Selecting one phrase keeps it fixed. Selecting two or more uses pure random once per actual morning playback; the same phrase may be selected on consecutive playbacks. Only the opening changes—the dynamic learner and course-time text still comes from the calendar. With no timed lessons, the Blueprint does not select or play an opening.

## Pre-class reminders and cancellation checks

The pre-class list also shows complete examples:

```text
☑ 提醒您，Grace 的 AmazingTalker 課程將在30分鐘後開始。
☑ 記得準備教材，再過30分鐘，Grace 的 AmazingTalker 課程就要開始了。
☐ 課程提醒，Grace 的 AmazingTalker 課程再過30分鐘就要開始了。
☐ 準備上課囉，Grace 的 AmazingTalker 課程將在30分鐘後開始。
☐ 別忘了，30分鐘後有 Grace 的 AmazingTalker 課程。
```

`Grace` and `30 minutes` are UI examples only. Actual playback substitutes the selected Calendar/account's `spoken_name` and the real remaining minutes. Stored values remain `preclass_standard`, `preclass_material`, `preclass_coming`, `preclass_ready`, and `preclass_short`, preserving v0.4.0 saved selections.

One selected style stays fixed. Two or more use pure random once after final verification for each actual playback; consecutive repeats are allowed. Every sentence in one merged playback uses the same selected style, while `{names}` and `{minutes}` remain dynamic.

`names` comes from `spoken_name` and identifies the AmazingTalker Calendar/account. v0.5.0 does not parse a teacher name from the event summary. The summary remains part of the fallback event identity used for cancellation and reschedule verification.

A one-minute heartbeat is required because Home Assistant cannot dynamically create calendar triggers from an arbitrary-length Blueprint input. Each run captures `check_time` and a fixed minute anchor, so a delayed older run never substitutes a new `now()`.

Heartbeat `calendar.get_events` calls only read Remote Calendar coordinator memory. `update_entity` is used only by the schedule, configured pre-class refresh, and final pre-play verification. Targets are de-duplicated inside each heartbeat.

Final verification prefers ICS `UID`; without UID it compares calendar entity, start, end, and summary. Missing means cancelled. A matching UID with changed start means moved, so the old time is not played. If refresh fails, `last_reported` does not advance, the calendar becomes unavailable, or the event cannot be confirmed, the affected reminder is skipped fail-closed. The Blueprint safely attempts a `system_log.write` warning.

Remote Calendar keeps UID internally, but the official `calendar.get_events` response currently omits UID. The Blueprint has a future-compatible UID path if the field becomes available; on current Home Assistant it therefore uses the documented calendar/start/end/summary fallback. This is an API limitation, not a hidden guarantee.

Normal minute-pattern execution evaluates an event/offset once and de-duplicates it in-run. A pure Blueprint creates no storage helper, so an exact-minute manual/external duplicate trigger is not persistently de-duplicated across restarts.

## Automation mode

The automation uses `parallel` with a limit of 10. `single` could drop the next heartbeat while TTS waits; `queued` could execute stale work late. `parallel` preserves each run's captured time and avoids a permanent queue; the cap bounds load.

## Multiple players, volume, and media resume

Each available player is snapshotted and receives independent volume, playback, and restore actions. An unknown, unavailable, or failing player does not block others. Different brands are not promised to be synchronized.

With restoration enabled, the Blueprint estimates a minimum speech duration, waits, lets buffering settle for up to 10 more seconds, then restores each reported original volume. Players expose no universal reliable “this TTS item ended” signal, so completion is best effort; missing `volume_level` is safely skipped.

`attempt_media_resume` and `restore_original_volume` are independent, supporting all four combinations.

> Media resume depends on player/integration support and cannot guarantee the song, position, or queue. Music Assistant and Announcement-capable players are more likely to succeed. Native HomePod, Siri, and direct iPhone AirPlay content may not resume. The Blueprint never guesses Apple Music URLs, queues, or positions from incomplete attributes.

## HomePod and Music Assistant notes

- HomePod Mini through the Apple TV integration is a formal manual-test target, but source-dependent state transitions require real-hardware verification.
- `announce: true` is only a request; unsupported integrations may play TTS without resuming media.
- Music Assistant Announcement generally has stronger resume support, but results still depend on provider and player.
- Multi-brand players may start and finish at different times.

## Diagnostic logging

Diagnostics are off by default. To troubleshoot, open **Settings → Automations & scenes**, edit the automation created from this Blueprint, expand **診斷紀錄與除錯**, enable logging, select `debug`, reproduce the issue, then return logging to off or `normal`.

Every entry is one JSON object in the Home Assistant raw system log under logger `blueprints.weihaochiu.amazingtalker_voice_reminder`. A run ID such as `20260821T183000000000-heartbeat` correlates scheduled refresh, cached query, targeted refresh, verification, TTS, player, and restore steps from one execution. Actions without an official success response use `action_dispatched` or `unknown`; continuing after an action is never reported as proof of success.

`safe` mode includes entity IDs, counts, times, remaining minutes, observable refresh/player state, and results. It omits learner names and event summaries. `detailed` may add those two fields, but replaces either field with `[redacted]` when it contains a URL or common credential marker. It never reads Remote Calendar integration config, and neither mode logs full TTS text.

Open **Settings → System → Logs** and use the full raw log to find the logger or run ID; the condensed view primarily retains recent warnings/errors. Safe-mode entries are designed for sharing with ChatGPT/Codex, although a final human review is still prudent. Review detailed-mode output manually before sharing.

The `diagnostic_log_retention_days` value is only written into the diagnostic header as a policy hint. It does **not** rotate or delete logs. A pure Blueprint has no filesystem API, the File integration targets a user-created fixed file, Recorder retention applies to the database rather than text logs, and a portable Blueprint cannot safely install a `shell_command`. See [Diagnostic Logging](docs/DIAGNOSTIC_LOGGING.md) for event codes, collection steps, privacy rules, and the exact retention boundary.

## Privacy and security

- Treat the AmazingTalker Calendar URL like a password.
- Never publish Home Assistant URLs/tokens, private network addresses, household entity IDs, learner names, or unredacted traces.
- Examples use obvious placeholders such as `calendar.amazingtalker_student_1` and `media_player.living_room_speaker`.
- Before contributing, run the privacy test and inspect `git diff`.

## Troubleshooting

- **No calendar entity:** create Remote Calendar first.
- **No events:** check Calendar dashboard, force one Remote Calendar update, and verify events are not all-day.
- **No speech:** check TTS entity/language and Home Assistant local URL reachability.
- **Skipped reminder:** inspect the trace for refresh timeout, unavailable calendar, cancellation/move, or no available player.
- **Volume mismatch:** the player may omit `volume_level`, exceed the bounded wait, or report TTS state unreliably.
- **No media resume:** disable `attempt_media_resume` if Announcement is not implemented correctly.
- **New lesson missing:** wait for or force a calendar update; see limitations.
- **Diagnostic collection:** enable `debug`, reproduce once, search the raw system log for the run ID, then disable debug.

## Test

```shell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m yamllint .
.venv/Scripts/python -m pytest -q
git diff --check
```

On Linux/macOS use `.venv/bin/python`. See [the Traditional Chinese manual checklist](docs/MANUAL_TEST_CHECKLIST.zh-TW.md). GitHub Actions repeats YAML, Blueprint static/Jinja, logic, privacy, UTF-8, and whitespace checks. The project never claims a Home Assistant runtime configuration check unless one actually ran in a supported Home Assistant/container environment.

## Update the Blueprint

Open **Settings → Automations & scenes → Blueprints**, open this Blueprint's menu, and choose **Re-import Blueprint**. Automations with an old scalar schedule must then reselect the structured schedule as described under “Upgrading an old schedule.”

This Blueprint does not automatically check for or install updates. The displayed version only identifies the Blueprint currently loaded by Home Assistant. Updating remains a manual **Re-import Blueprint** action.

### How to confirm that the Blueprint is updated

After re-importing, open the automation editor and confirm both visible markers:

- Blueprint title: `AmazingTalker 多學員課程語音提醒 · v0.5.0`
- First section description: `目前 Blueprint：v0.5.0`

If an older version is still shown, go to **Settings → Automations & scenes → Blueprints**, select the three-dot menu for the AmazingTalker Blueprint, choose **Re-import blueprint**, and then reopen the automation. Home Assistant documents this as the supported update path for imported community Blueprints.

## Known limitations

- A morning-cached cancellation can be suppressed after a successful pre-class refresh or final verification.
- A completely new lesson absent from old cache cannot trigger its own discovery refresh; it depends on built-in polling or scheduled refresh.
- The official `calendar.get_events` response does not currently expose Remote Calendar UID, so current confirmation uses calendar/start/end/summary; UID matching activates only if that field becomes available.
- If a lesson moves earlier and refresh occurs after a reminder point, past reminders are not backfilled.
- Pure Blueprint state cannot provide a persistent event ledger for exact-minute external duplicate triggers.
- TTS end detection, volume restoration, media resume, and HomePod behavior are player-dependent best efforts.
- `diagnostic_log_retention_days` is a metadata hint only; this Blueprint cannot create daily files or enforce N-day cleanup.
- Home Assistant system-log rotation and any optional file-notification retention are installation-managed.
- Final runtime behavior needs the user's real Home Assistant, TTS provider, calendars, and speakers.

## Technical basis

Only official sources are used: [AmazingTalker calendar instructions](https://amazingtalker.elevio.help/en/articles/248-how-do-i-connect-with-my-online-calendar), [Blueprint schema](https://www.home-assistant.io/docs/blueprint/schema/), [selectors](https://www.home-assistant.io/docs/blueprint/selectors/), [Remote Calendar](https://www.home-assistant.io/integrations/remote_calendar/), [`calendar.get_events`](https://www.home-assistant.io/actions/calendar.get_events/), [TTS](https://www.home-assistant.io/integrations/tts), [`media_player.play_media`](https://www.home-assistant.io/actions/media_player.play_media/), [System Log](https://www.home-assistant.io/integrations/system_log/), [automation traces](https://www.home-assistant.io/docs/automation/troubleshooting/), [File](https://www.home-assistant.io/integrations/file), [Recorder](https://www.home-assistant.io/integrations/recorder), [Shell Command](https://www.home-assistant.io/integrations/shell_command), and [Music Assistant announcements](https://www.music-assistant.io/faq/announcement/).

## Version and license

Current Blueprint version: `v0.5.0`; see [CHANGELOG.md](CHANGELOG.md). Licensed under [MIT](LICENSE), © 2026 weihaochiu.
