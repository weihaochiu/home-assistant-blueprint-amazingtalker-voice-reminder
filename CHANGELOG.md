# Changelog

All notable changes to this project are documented here.

## [0.1.0] - Unreleased

### Added

- Initial development version of the AmazingTalker multi-learner voice reminder Blueprint.
- Scheduled calendar refresh, morning summaries, configurable pre-class reminders, cancellation verification, multi-player TTS, volume restoration, tests, and documentation.

### Changed

- Redesigned scheduled refresh configuration using the Home Assistant choose selector.
- Weekly refresh now supports multiple weekdays, and monthly refresh supports multiple month days.
- Monthly dates beyond the end of shorter months fall back to that month's final day and collapse to one refresh when multiple selections resolve to the same date.
- Irrelevant weekly and monthly fields are no longer shown for other schedule modes.
- Reused the reminder heartbeat for scheduled refresh while keeping both flows independent.
- Raised the minimum Home Assistant version to 2026.1.0 and retained legacy scalar schedule compatibility.
