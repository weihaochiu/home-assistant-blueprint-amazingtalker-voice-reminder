# AmazingTalker Multi-Learner Voice Reminder

[繁體中文](README.zh-TW.md)

[![Open your Home Assistant instance and import this Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fweihaochiu%2Fhome-assistant-blueprint-amazingtalker-voice-reminder%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fweihaochiu%2Famazingtalker_voice_reminder.yaml)

A Home Assistant Automation Blueprint that combines any number of AmazingTalker learner calendars into natural Traditional Chinese morning summaries and pre-class voice reminders.

This is an independent community project. It is not an official AmazingTalker project and is not affiliated with or endorsed by AmazingTalker.

## Features

- Add any number of learners using the repeatable Home Assistant object selector.
- Read each Remote Calendar coordinator cache every minute without downloading ICS every minute.
- Optional daily, weekly, or monthly forced refresh with end-of-month fallback.
- Morning summary covering every timed lesson for every learner; all-day events are ignored.
- Any number of normalized pre-class reminder offsets, targeted refresh, and fail-closed final verification.
- Match by ICS UID, with calendar/start/end/summary fallback when UID is absent.
- Merge simultaneous lessons and different offsets into one playback request with natural sentences.
- Independent multi-player playback, per-player volume restoration, and optional announcement resume.

## Requirements

- Home Assistant 2026.1.0 or newer. The choose selector used by the conditional schedule form was introduced in Home Assistant 2026.1.
- One Home Assistant Remote Calendar entry per learner.
- At least one `media_player` and one `tts` entity. Google Translate TTS is the first formal target.
- The player must be able to fetch TTS media from Home Assistant. Check **Settings → System → Network** if generated speech cannot play.
- HACS is not used. This repository contains no custom integration or `hacs.json`.

## Create the Remote Calendars

The Blueprint does not create Remote Calendar entries.

1. Open **Settings → Devices & services → Add integration**.
2. Add **Remote Calendar**.
3. Create a separate entry for each learner and paste that learner's AmazingTalker ICS URL.
4. Leave username and password empty; the AmazingTalker URL itself supplies the private read key.
5. Select the generated `calendar.*` entity, for example `calendar.amazingtalker_student_1`, in the Blueprint.

> The AmazingTalker ICS URL is a private read key. Never commit it, put it in a GitHub Issue, or post it publicly. A documentation-only placeholder is `https://api.amazingtalker.com/v1/user/calendar/REPLACE_WITH_YOUR_PRIVATE_TOKEN`.

Remote Calendar normally polls every 24 hours. The Blueprint's schedule is an additional forced update and cannot reduce the integration's built-in polling frequency.

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
| `update_time` | `07:00:00` | Legacy compatibility value used only by existing scalar schedules. |
| `update_weekday` | `monday` | Legacy compatibility value used only by existing scalar weekly schedules. |
| `update_month_day` | `1` | Legacy compatibility value used only by existing scalar monthly schedules. |
| `enable_morning_summary` | `true` | Enable the local-day morning summary. |
| `morning_summary_time` | `07:12:00` | Ignored when morning summary is disabled. |
| `enable_pre_class_reminders` | `true` | Enable heartbeat-based reminders. |
| `reminder_offsets` | `30`, `10` | Repeatable minutes-before entries; runtime values become positive unique integers sorted descending without rewriting UI data. |
| `enable_pre_class_refresh` | `true` | Refresh only calendars whose cached lesson reaches the refresh point. |
| `pre_class_refresh_minutes` | `60` | Minutes before class for targeted refresh. |
| `verify_before_each_reminder` | `true` | Refresh and confirm immediately before playback; failure skips the affected reminder. |

Input keys remain backward compatible. Future optional inputs will have defaults so existing automations keep loading.

## Update schedule

- **Daily:** only the update time is shown. For example, `07:00` refreshes every day at 07:00.
- **Weekly:** the update time and a multiple-choice weekday field are shown. For example, Monday, Wednesday, and Friday at `07:00` refreshes on all three selected weekdays.
- **Monthly:** the update time and a multiple-choice day field are shown. For example, 1, 15, and 30 at `07:00` refreshes on all three selected dates.
- If a selected day 29, 30, or 31 does not exist, it falls back to that month's final day. Multiple selected dates that fall back to the same day are de-duplicated, so February receives one refresh for that minute.
- Empty weekly or monthly selections fail safe and do not run a scheduled refresh.

The existing one-minute heartbeat performs the scheduled check. It compares the local `HH:MM`, so the matching minute causes at most one scheduled refresh action. Scheduled refresh and pre-class refresh/reminder work remain independent within the same heartbeat.

The scheduled forced refresh only makes an additional Remote Calendar update request. It cannot reduce the Remote Calendar integration's own built-in polling interval.

### Existing automation migration

The `update_frequency` input ID is retained. Existing automations whose value is the legacy `daily`, `weekly`, or `monthly` scalar continue to use their saved `update_time`, `update_weekday`, and `update_month_day` values. Those legacy inputs remain in a collapsed compatibility section so new users get the conditional schedule form. When editing an upgraded automation, reselect **Update schedule** once to migrate its form value to the new structured format; the runtime legacy schedule remains unchanged until then.

## Morning summary

At the selected local time, `calendar.get_events` queries local 00:00 through the next local 00:00. Timed events are sorted by start and learner; all lessons are spoken. Name fallback is non-blank `spoken_name`, calendar `friendly_name`, then entity ID without `calendar.`. Times are natural: `08:00` → `早上8點`, `13:30` → `下午1點30分`, `20:00` → `晚上8點`. With no lessons, volume and TTS are untouched.

## Pre-class reminders and cancellation checks

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

## Privacy and security

- Treat the ICS URL token like a password.
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

Open **Settings → Automations & scenes → Blueprints**, open this Blueprint's menu, and choose **Re-import Blueprint**. Review release notes first. Re-import overwrites the stored Blueprint while retaining compatible automation inputs.

## Known limitations

- A morning-cached cancellation can be suppressed after a successful pre-class refresh or final verification.
- A completely new lesson absent from old cache cannot trigger its own discovery refresh; it depends on built-in polling or scheduled refresh.
- The official `calendar.get_events` response does not currently expose Remote Calendar UID, so current confirmation uses calendar/start/end/summary; UID matching activates only if that field becomes available.
- If a lesson moves earlier and refresh occurs after a reminder point, past reminders are not backfilled.
- Pure Blueprint state cannot provide a persistent event ledger for exact-minute external duplicate triggers.
- TTS end detection, volume restoration, media resume, and HomePod behavior are player-dependent best efforts.
- Final runtime behavior needs the user's real Home Assistant, TTS provider, calendars, and speakers.

## Technical basis

Only official sources are used: [Blueprint schema](https://www.home-assistant.io/docs/blueprint/schema/), [selectors](https://www.home-assistant.io/docs/blueprint/selectors/), [Remote Calendar](https://www.home-assistant.io/integrations/remote_calendar/), [`calendar.get_events`](https://www.home-assistant.io/actions/calendar.get_events/), [TTS](https://www.home-assistant.io/integrations/tts), [`media_player.play_media`](https://www.home-assistant.io/actions/media_player.play_media/), and [Music Assistant announcements](https://www.music-assistant.io/faq/announcement/).

## Version and license

Development version: `0.1.0` (Unreleased); see [CHANGELOG.md](CHANGELOG.md). Licensed under [MIT](LICENSE), © 2026 weihaochiu.
