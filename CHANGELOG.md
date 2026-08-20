# Changelog

All notable changes to this project are documented here.

## v0.4.0 - 2026-08-21

### Added

- Initial development version of the AmazingTalker multi-learner voice reminder Blueprint.
- Scheduled calendar refresh, morning summaries, configurable pre-class reminders, cancellation verification, multi-player TTS, volume restoration, tests, and documentation.
- Visible v0.4.0 information in the Blueprint title, description, and first input section.
- Selectable built-in morning announcement phrases.
- Selectable built-in pre-class reminder phrases.
- Pure random phrase selection when multiple phrases are selected.

### Changed

- Redesigned scheduled refresh configuration using the Home Assistant choose selector.
- Weekly refresh now supports multiple weekdays, and monthly refresh supports multiple month days.
- Monthly dates beyond the end of shorter months fall back to that month's final day and collapse to one refresh when multiple selections resolve to the same date.
- Irrelevant weekly and monthly fields are no longer shown for other schedule modes.
- Reused the reminder heartbeat for scheduled refresh while keeping both flows independent.
- Raised the minimum Home Assistant version to 2026.1.0.
- Removed the legacy scheduled-refresh compatibility section and its `update_time`, `update_weekday`, and `update_month_day` inputs.
- Scheduled refresh now accepts only the structured daily, weekly, or monthly choose-selector value; legacy scalar or malformed values fail safe without running a scheduled refresh.
- Confirmed from Home Assistant 2026.1.0 source that stale removed input keys are accepted and ignored, while users must resave a structured schedule to restore scheduled refresh.
- One selected phrase remains fixed; multiple selected phrases may repeat consecutively by design.

### Safety

- Legacy scalar scheduled-refresh values remain fail-safe and do not run scheduled refresh.
- Added a local-midnight, normally once-daily `system_log` migration warning for a recognized legacy scalar schedule.
- Morning summaries and pre-class workflows remain active while a legacy scheduled-refresh value waits for migration.

### Documentation

- Expanded the AmazingTalker Account Settings → Connect to Calendar → Copy URL → Home Assistant Remote Calendar setup guide.
- Added field-by-field Remote Calendar instructions, private URL handling, calendar entity verification, multi-learner examples, and first-time troubleshooting.
