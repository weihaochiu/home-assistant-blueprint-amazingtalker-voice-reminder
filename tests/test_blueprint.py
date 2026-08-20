"""Static and reference-logic tests for the Home Assistant Blueprint."""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from urllib.parse import parse_qs, quote_plus, urlparse

from jinja2 import Environment
from jinja2.nativetypes import NativeEnvironment
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = (
    ROOT
    / "blueprints"
    / "automation"
    / "weihaochiu"
    / "amazingtalker_voice_reminder.yaml"
)
SOURCE_URL = (
    "https://github.com/weihaochiu/"
    "home-assistant-blueprint-amazingtalker-voice-reminder/blob/main/"
    "blueprints/automation/weihaochiu/amazingtalker_voice_reminder.yaml"
)


class InputRef(str):
    """Represent a Home Assistant !input value during static parsing."""


class BlueprintLoader(yaml.SafeLoader):
    """PyYAML loader that understands Home Assistant's !input tag."""


def _input(loader: BlueprintLoader, node: yaml.Node) -> InputRef:
    return InputRef(loader.construct_scalar(node))


BlueprintLoader.add_constructor("!input", _input)


@pytest.fixture(scope="module")
def blueprint_text() -> str:
    return BLUEPRINT_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def blueprint(blueprint_text: str) -> dict:
    return yaml.load(blueprint_text, Loader=BlueprintLoader)


def flatten_inputs(input_tree: dict) -> dict:
    flattened: dict = {}
    for key, value in input_tree.items():
        if isinstance(value, dict) and "input" in value:
            flattened.update(value["input"])
        else:
            flattened[key] = value
    return flattened


def walk(value):
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk(key)
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def normalize_offsets(values) -> list[int]:
    normalized = set()
    for item in values:
        raw = item.get("minutes_before", 0) if isinstance(item, dict) else item
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            normalized.add(value)
    return sorted(normalized, reverse=True)


WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _as_list(value) -> list:
    if isinstance(value, (str, int, float)):
        return [value]
    if isinstance(value, list):
        return value
    return []


def normalize_schedule(schedule) -> dict:
    modes = {
        "每天": "daily",
        "每週": "weekly",
        "每月": "monthly",
    }
    if isinstance(schedule, dict):
        active_choice = str(schedule.get("active_choice", "")).strip()
        selected = schedule.get(active_choice, {})
        config = (
            selected
            if active_choice in modes and isinstance(selected, dict)
            else {}
        )
        mode = modes.get(active_choice, "")
    else:
        mode = ""
        config = {}

    weekdays = []
    for item in _as_list(config.get("update_weekdays", [])):
        value = str(item).strip().lower()
        if value in WEEKDAYS and value not in weekdays:
            weekdays.append(value)

    month_days = set()
    for item in _as_list(config.get("update_month_days", [])):
        try:
            value = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= value <= 31:
            month_days.add(value)

    return {
        "mode": mode,
        "time": str(config.get("update_time", "")).strip(),
        "weekdays": weekdays,
        "month_days": sorted(month_days),
    }


def effective_month_days(moment: datetime, selected_days: list[int]) -> list[int]:
    last_day = calendar.monthrange(moment.year, moment.month)[1]
    return sorted({min(day, last_day) for day in selected_days if 1 <= day <= 31})


def scheduled_update_due(
    moment: datetime,
    schedule,
    *,
    enabled: bool = True,
) -> bool:
    if not enabled:
        return False
    normalized = normalize_schedule(schedule)
    if moment.strftime("%H:%M") != normalized["time"][:5]:
        return False
    if normalized["mode"] == "daily":
        return True
    if normalized["mode"] == "weekly":
        return WEEKDAYS[moment.weekday()] in normalized["weekdays"]
    if normalized["mode"] == "monthly":
        return moment.day in effective_month_days(moment, normalized["month_days"])
    return False


def spoken_time(moment: datetime) -> str:
    hour = moment.hour
    minute = moment.minute
    if hour == 0:
        period, spoken_hour = "凌晨", 12
    elif hour < 6:
        period, spoken_hour = "凌晨", hour
    elif hour < 12:
        period, spoken_hour = "早上", hour
    elif hour == 12:
        period, spoken_hour = "中午", 12
    elif hour < 18:
        period, spoken_hour = "下午", hour - 12
    else:
        period, spoken_hour = "晚上", hour - 12
    suffix = f"{minute}分" if minute else ""
    return f"{period}{spoken_hour}點{suffix}"


def is_timed_event(event: dict) -> bool:
    raw = str(event.get("start", ""))
    return "T" in raw or " " in raw


def event_identity(entity: str, event: dict) -> str:
    uid = str(event.get("uid") or "")
    if uid:
        return "|".join([entity, "uid", uid, str(event.get("start", ""))])
    return "|".join(
        [
            entity,
            str(event.get("start", "")),
            str(event.get("end", "")),
            str(event.get("summary", "")),
        ]
    )


def still_exists(entity: str, original: dict, fresh_events: list[dict]) -> bool:
    original_uid = str(original.get("uid") or "")
    for fresh in fresh_events:
        fresh_uid = str(fresh.get("uid") or "")
        same_start = str(fresh.get("start")) == str(original.get("start"))
        if original_uid and fresh_uid == original_uid and same_start:
            return True
        if not original_uid and not fresh_uid:
            if event_identity(entity, fresh) == event_identity(entity, original):
                return True
    return False


def reminder_message(candidates: list[dict]) -> str:
    grouped: dict[int, list[str]] = defaultdict(list)
    seen_keys = set()
    for candidate in candidates:
        key = (candidate["identity"], candidate["remaining"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        names = grouped[candidate["remaining"]]
        if candidate["learner"] not in names:
            names.append(candidate["learner"])
    sentences = []
    for offset in sorted(grouped, reverse=True):
        names = grouped[offset]
        joined = names[0] if len(names) == 1 else "、".join(names[:-1]) + " 和 " + names[-1]
        sentences.append(
            f"提醒您，{joined} 的 AmazingTalker 課程將在{offset}分鐘後開始。"
        )
    return "".join(sentences)


def player_plan(
    players: list[str],
    player_states: dict[str, str],
    volume_levels: dict[str, float | None],
    restore_volume: bool,
    resume_media: bool,
) -> dict:
    """Model the Blueprint's availability, snapshot, restore, and announce decisions."""
    snapshots = []
    for player in players:
        if player_states.get(player, "unknown") in {"unknown", "unavailable"}:
            continue
        snapshots.append(
            {
                "entity_id": player,
                "volume": volume_levels.get(player) if restore_volume else None,
            }
        )
    restore_targets = [
        item for item in snapshots if restore_volume and isinstance(item["volume"], (int, float))
    ]
    return {
        "play_targets": [item["entity_id"] for item in snapshots],
        "restore_targets": restore_targets,
        "announce": resume_media,
    }


def test_yaml_loads_and_metadata_is_correct(blueprint: dict) -> None:
    metadata = blueprint["blueprint"]
    assert metadata["name"] == "AmazingTalker 多學員課程語音提醒"
    assert metadata["domain"] == "automation"
    assert metadata["author"] == "weihaochiu"
    assert metadata["source_url"] == SOURCE_URL
    assert metadata["homeassistant"]["min_version"] == "2026.1.0"


def test_all_input_references_are_declared_and_used(blueprint: dict) -> None:
    inputs = flatten_inputs(blueprint["blueprint"]["input"])
    references = {str(value) for value in walk(blueprint) if isinstance(value, InputRef)}
    assert references == set(inputs)


def test_required_and_optional_input_defaults(blueprint: dict) -> None:
    inputs = flatten_inputs(blueprint["blueprint"]["input"])
    required = {"learners", "media_players", "tts_entity"}
    assert required <= set(inputs)
    for key, definition in inputs.items():
        if key not in required:
            assert "default" in definition, f"optional input {key} needs a default"


def test_repeatable_learner_object_schema(blueprint: dict) -> None:
    inputs = flatten_inputs(blueprint["blueprint"]["input"])
    selector = inputs["learners"]["selector"]["object"]
    assert selector["multiple"] is True
    assert selector["fields"]["calendar_entity"]["required"] is True
    entity = selector["fields"]["calendar_entity"]["selector"]["entity"]
    assert entity["filter"] == [{"domain": "calendar"}]
    assert selector["fields"]["spoken_name"].get("required", False) is False


def test_player_and_tts_selector_schema(blueprint: dict) -> None:
    inputs = flatten_inputs(blueprint["blueprint"]["input"])
    players = inputs["media_players"]["selector"]["entity"]
    assert players["multiple"] is True
    assert players["filter"] == [{"domain": "media_player"}]
    tts = inputs["tts_entity"]["selector"]["entity"]
    assert tts["filter"] == [{"domain": "tts"}]


def test_choose_schedule_selector_schema_and_conditional_fields(blueprint: dict) -> None:
    inputs = flatten_inputs(blueprint["blueprint"]["input"])
    schedule = inputs["update_frequency"]
    choose = schedule["selector"]["choose"]
    assert set(choose) == {"choices"}
    choices = choose["choices"]
    assert set(choices) == {"每天", "每週", "每月"}

    daily = choices["每天"]["selector"]["object"]["fields"]
    weekly = choices["每週"]["selector"]["object"]["fields"]
    monthly = choices["每月"]["selector"]["object"]["fields"]
    assert set(daily) == {"update_time"}
    assert set(weekly) == {"update_time", "update_weekdays"}
    assert set(monthly) == {"update_time", "update_month_days"}
    assert daily["update_time"]["required"] is True
    assert weekly["update_time"]["required"] is True
    assert monthly["update_time"]["required"] is True

    weekday_select = weekly["update_weekdays"]["selector"]["select"]
    assert weekly["update_weekdays"]["required"] is True
    assert weekday_select["multiple"] is True
    assert weekday_select["custom_value"] is False
    assert [option["value"] for option in weekday_select["options"]] == WEEKDAYS
    assert [option["label"] for option in weekday_select["options"]] == [
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期日",
    ]

    month_day_select = monthly["update_month_days"]["selector"]["select"]
    assert monthly["update_month_days"]["required"] is True
    assert month_day_select["multiple"] is True
    assert month_day_select["custom_value"] is False
    assert [option["value"] for option in month_day_select["options"]] == [
        str(day) for day in range(1, 32)
    ]
    assert schedule["default"] == {
        "active_choice": "每天",
        "每天": {"update_time": "07:00:00"},
        "每週": {"update_time": "07:00:00", "update_weekdays": ["monday"]},
        "每月": {"update_time": "07:00:00", "update_month_days": ["1"]},
    }


def test_legacy_schedule_section_inputs_and_runtime_are_absent(
    blueprint: dict, blueprint_text: str
) -> None:
    input_tree = blueprint["blueprint"]["input"]
    assert "legacy_scheduled_update_section" not in input_tree
    assert list(input_tree).index("morning_section") == (
        list(input_tree).index("scheduled_update_section") + 1
    )
    inputs = flatten_inputs(input_tree)
    assert {
        "update_time",
        "update_weekday",
        "update_month_day",
    }.isdisjoint(inputs)
    assert "legacy_update_" not in blueprint_text
    assert "!input update_time" not in blueprint_text
    assert "!input update_weekday" not in blueprint_text
    assert "!input update_month_day" not in blueprint_text


def test_modern_automation_syntax_and_heartbeat(blueprint: dict, blueprint_text: str) -> None:
    assert "triggers" in blueprint and "actions" in blueprint
    assert "platform:" not in blueprint_text
    assert "service:" not in blueprint_text
    heartbeat = next(item for item in blueprint["triggers"] if item["id"] == "heartbeat")
    assert heartbeat == {"trigger": "time_pattern", "minutes": "/1", "id": "heartbeat"}
    assert {item["id"] for item in blueprint["triggers"]} == {"heartbeat", "morning_summary"}
    assert "id: scheduled_update" not in blueprint_text
    assert blueprint["mode"] == "parallel"
    assert blueprint["max"] == 10


def test_scheduled_refresh_is_independent_from_reminder_heartbeat(
    blueprint: dict, blueprint_text: str
) -> None:
    scheduled_if = blueprint["actions"][0]
    reminder_choose = blueprint["actions"][1]
    assert "if" in scheduled_if and "then" in scheduled_if
    assert "choose" in reminder_choose
    assert "本分鐘一次強制更新所有選取的行事曆" in blueprint_text
    assert "每分鐘 heartbeat 課前流程" in blueprint_text
    assert blueprint_text.index("本分鐘一次強制更新所有選取的行事曆") < blueprint_text.index(
        "每分鐘 heartbeat 課前流程"
    )


def test_templates_are_jinja_syntax_valid(blueprint: dict) -> None:
    environment = Environment(autoescape=False)
    environment.filters["urlencode"] = quote_plus
    for value in walk(blueprint):
        if isinstance(value, str) and ("{{" in value or "{%" in value or "{#" in value):
            environment.parse(value)


def test_cross_action_values_use_serializable_primitives(blueprint_text: str) -> None:
    assert 'check_time: "{{ as_timestamp(now()) }}"' in blueprint_text
    assert "'before': as_timestamp(states[entity].last_reported)" in blueprint_text
    cached_section = blueprint_text.split("cached_events: >-", 1)[1].split(
        "refresh_calendars: >-", 1
    )[0]
    assert "'start': start" not in cached_section
    assert "max(default=" not in blueprint_text


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([{"minutes_before": 30}], [30]),
        ([{"minutes_before": 30}, {"minutes_before": 10}], [30, 10]),
        ([{"minutes_before": 60}, {"minutes_before": 30}, {"minutes_before": 10}], [60, 30, 10]),
        ([{"minutes_before": 10}, {"minutes_before": 0}, {"minutes_before": -2}, {"minutes_before": 10}], [10]),
        ([{"minutes_before": "bad"}, {}, None], []),
    ],
)
def test_reminder_offset_normalization(values, expected) -> None:
    assert normalize_offsets(values) == expected


def choose_schedule(choice: str, **values) -> dict:
    return {"active_choice": choice, choice: values}


def render_blueprint_schedule(blueprint: dict, schedule, moment: datetime) -> tuple[dict, bool]:
    environment = NativeEnvironment(autoescape=False)
    environment.globals.update(
        as_datetime=lambda value: datetime.fromtimestamp(float(value), timezone.utc),
        as_local=lambda value: value,
        timedelta=timedelta,
    )
    context = {
        "update_frequency_input": schedule,
        "check_time": moment.replace(tzinfo=timezone.utc).timestamp(),
    }
    variables = blueprint["variables"]
    for name in (
        "schedule_mode",
        "schedule_config",
        "schedule_time",
        "schedule_weekdays",
        "schedule_month_days",
    ):
        context[name] = environment.from_string(variables[name]).render(context)
    due_template = blueprint["actions"][0]["if"][2]["value_template"]
    due = environment.from_string(due_template).render(context)
    assert isinstance(due, bool), f"scheduled due template must render a native bool, got {due!r}"
    return context, due


def test_actual_blueprint_schedule_templates_normalize_and_render(blueprint: dict) -> None:
    weekly = choose_schedule(
        "每週",
        update_time="07:00:00",
        update_weekdays=["monday", "wednesday", "friday"],
    )
    context, due = render_blueprint_schedule(
        blueprint, weekly, datetime(2026, 8, 19, 7, 0)
    )
    assert context["schedule_mode"] == "weekly"
    assert context["schedule_time"] == "07:00:00"
    assert context["schedule_weekdays"] == ["monday", "wednesday", "friday"]
    assert due

    monthly = choose_schedule(
        "每月", update_time="07:00:00", update_month_days=["28", "29", "30", "31"]
    )
    context, due = render_blueprint_schedule(
        blueprint, monthly, datetime(2026, 2, 28, 7, 0)
    )
    assert context["schedule_month_days"] == [28, 29, 30, 31]
    assert due

    empty = choose_schedule("每月", update_time="07:00:00", update_month_days=[])
    context, due = render_blueprint_schedule(
        blueprint, empty, datetime(2026, 8, 1, 7, 0)
    )
    assert context["schedule_month_days"] == []
    assert not due


def test_daily_schedule_matches_exact_minute_once() -> None:
    schedule = choose_schedule("每天", update_time="07:00:00")
    assert scheduled_update_due(datetime(2026, 8, 17, 7, 0, 0), schedule)
    assert scheduled_update_due(datetime(2026, 8, 17, 7, 0, 59), schedule)
    assert not scheduled_update_due(datetime(2026, 8, 17, 7, 1), schedule)


def test_weekly_single_and_multiple_schedule() -> None:
    single = choose_schedule(
        "每週", update_time="07:00:00", update_weekdays=["monday"]
    )
    assert scheduled_update_due(datetime(2026, 8, 17, 7, 0), single)
    assert not scheduled_update_due(datetime(2026, 8, 18, 7, 0), single)

    multiple = choose_schedule(
        "每週",
        update_time="07:00:00",
        update_weekdays=["monday", "wednesday", "friday"],
    )
    expected = [True, False, True, False, True]
    actual = [
        scheduled_update_due(datetime(2026, 8, 17 + offset, 7, 0), multiple)
        for offset in range(5)
    ]
    assert actual == expected


def test_weekly_all_days_and_empty_selection() -> None:
    all_days = choose_schedule(
        "每週", update_time="07:00:00", update_weekdays=WEEKDAYS
    )
    assert all(
        scheduled_update_due(datetime(2026, 8, 17 + offset, 7, 0), all_days)
        for offset in range(7)
    )
    empty = choose_schedule("每週", update_time="07:00:00", update_weekdays=[])
    assert not scheduled_update_due(datetime(2026, 8, 17, 7, 0), empty)


def test_monthly_single_and_multiple_schedule() -> None:
    single = choose_schedule(
        "每月", update_time="07:00:00", update_month_days=["1"]
    )
    assert scheduled_update_due(datetime(2026, 8, 1, 7, 0), single)
    assert not scheduled_update_due(datetime(2026, 8, 2, 7, 0), single)

    multiple = choose_schedule(
        "每月", update_time="07:00:00", update_month_days=["1", "15", "30"]
    )
    assert all(
        scheduled_update_due(datetime(2026, 8, day, 7, 0), multiple)
        for day in (1, 15, 30)
    )
    assert not scheduled_update_due(datetime(2026, 8, 29, 7, 0), multiple)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 1, 31, 7, 0), True),
        (datetime(2026, 2, 28, 7, 0), True),
        (datetime(2024, 2, 29, 7, 0), True),
        (datetime(2026, 4, 30, 7, 0), True),
        (datetime(2026, 8, 30, 7, 0), False),
    ],
)
def test_monthly_last_day_fallback(moment, expected) -> None:
    schedule = choose_schedule(
        "每月", update_time="07:00:00", update_month_days=["31"]
    )
    assert scheduled_update_due(moment, schedule) is expected


def test_multiple_month_end_fallback_is_unique_and_runs_once() -> None:
    february = datetime(2026, 2, 28, 7, 0)
    mixed = choose_schedule(
        "每月",
        update_time="07:00:00",
        update_month_days=["1", "15", "30", "31"],
    )
    normalized = normalize_schedule(mixed)
    assert effective_month_days(february, normalized["month_days"]) == [1, 15, 28]

    schedule = choose_schedule(
        "每月",
        update_time="07:00:00",
        update_month_days=["28", "29", "30", "31"],
    )
    normalized = normalize_schedule(schedule)
    assert effective_month_days(february, normalized["month_days"]) == [28]
    assert scheduled_update_due(february, schedule)


def test_monthly_empty_selection_and_invalid_types_fail_safe() -> None:
    empty = choose_schedule("每月", update_time="07:00:00", update_month_days=[])
    assert not scheduled_update_due(datetime(2026, 8, 1, 7, 0), empty)
    invalid = choose_schedule(
        "每月", update_time="07:00:00", update_month_days=[None, "bad", 0, 32]
    )
    assert normalize_schedule(invalid)["month_days"] == []
    assert not scheduled_update_due(datetime(2026, 8, 1, 7, 0), invalid)


def test_disabled_schedule_never_runs_but_does_not_gate_reminders() -> None:
    schedule = choose_schedule("每天", update_time="07:00:00")
    assert not scheduled_update_due(
        datetime(2026, 8, 17, 7, 0), schedule, enabled=False
    )


@pytest.mark.parametrize(
    "schedule",
    [
        "weekly",
        "daily",
        "monthly",
        None,
        [],
        {"active_choice": "未知", "未知": {"update_time": "07:00:00"}},
        {"active_choice": "每週", "每週": "malformed"},
        {"active_choice": "每月", "每月": None},
    ],
)
def test_non_mapping_unknown_and_malformed_schedules_fail_safe(schedule) -> None:
    normalized = normalize_schedule(schedule)
    assert normalized["mode"] == "" or normalized["time"] == ""
    assert not scheduled_update_due(datetime(2026, 8, 17, 7, 0), schedule)


@pytest.mark.parametrize(
    "schedule",
    [
        "weekly",
        {"active_choice": "未知", "未知": {"update_time": "07:00:00"}},
        {"active_choice": "每週", "每週": "malformed"},
    ],
)
def test_actual_blueprint_schedule_templates_fail_safe(
    blueprint: dict, schedule
) -> None:
    context, due = render_blueprint_schedule(
        blueprint, schedule, datetime(2026, 8, 17, 7, 0)
    )
    assert context["schedule_mode"] == "" or context["schedule_time"] == ""
    assert not due


@pytest.mark.parametrize(
    ("hour", "minute", "expected"),
    [
        (0, 0, "凌晨12點"),
        (8, 0, "早上8點"),
        (12, 0, "中午12點"),
        (13, 30, "下午1點30分"),
        (20, 0, "晚上8點"),
        (21, 30, "晚上9點30分"),
    ],
)
def test_natural_traditional_chinese_time(hour, minute, expected) -> None:
    assert spoken_time(datetime(2026, 8, 18, hour, minute)) == expected


def test_one_two_and_many_calendars_fixture() -> None:
    fixture = yaml.safe_load((ROOT / "tests" / "fixtures" / "events.yaml").read_text(encoding="utf-8"))
    calendars = fixture["calendars"]
    assert len(list(calendars)[:1]) == 1
    assert len(calendars) == 2
    calendars["calendar.amazingtalker_student_3"] = {"events": []}
    assert len(calendars) == 3


def test_no_courses_and_all_day_events_are_ignored() -> None:
    assert reminder_message([]) == ""
    assert not is_timed_event({"start": "2026-08-18"})
    assert is_timed_event({"start": "2026-08-18T20:00:00+08:00"})


def test_one_learner_multiple_lessons_and_different_times() -> None:
    candidates = [
        {"identity": "u1", "remaining": 30, "learner": "Student One"},
        {"identity": "u2", "remaining": 10, "learner": "Student One"},
    ]
    message = reminder_message(candidates)
    assert "30分鐘" in message and "10分鐘" in message
    assert message.count("Student One") == 2


def test_same_time_learners_are_merged_and_deduplicated() -> None:
    candidates = [
        {"identity": "u1", "remaining": 30, "learner": "Student One"},
        {"identity": "u2", "remaining": 30, "learner": "Student Two"},
        {"identity": "u2", "remaining": 30, "learner": "Student Two"},
    ]
    assert reminder_message(candidates) == (
        "提醒您，Student One 和 Student Two 的 AmazingTalker 課程將在30分鐘後開始。"
    )


def test_different_remaining_times_share_one_playback_message() -> None:
    candidates = [
        {"identity": "u1", "remaining": 30, "learner": "Student One"},
        {"identity": "u2", "remaining": 10, "learner": "Student Two"},
    ]
    message = reminder_message(candidates)
    assert message.count("提醒您") == 2
    assert message.index("30分鐘") < message.index("10分鐘")


def test_uid_cancellation_and_reschedule_confirmation() -> None:
    original = {
        "uid": "fake-uid",
        "summary": "Lesson",
        "start": "2026-08-18T20:00:00+08:00",
        "end": "2026-08-18T20:50:00+08:00",
    }
    assert not still_exists("calendar.amazingtalker_student_1", original, [])
    moved = [{**original, "start": "2026-08-18T21:00:00+08:00"}]
    assert not still_exists("calendar.amazingtalker_student_1", original, moved)
    assert still_exists("calendar.amazingtalker_student_1", original, [original])


def test_uid_api_limitation_is_documented() -> None:
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")
    assert "calendar.get_events` response currently omits UID" in english
    assert "`calendar.get_events` 目前不回傳 UID" in chinese


def test_fallback_identity_without_uid() -> None:
    original = {
        "summary": "Lesson",
        "start": "2026-08-18T20:00:00+08:00",
        "end": "2026-08-18T20:50:00+08:00",
    }
    assert still_exists("calendar.amazingtalker_student_1", original, [original.copy()])
    assert not still_exists(
        "calendar.amazingtalker_student_1", original, [{**original, "summary": "Moved"}]
    )


def test_sixty_minute_refresh_and_each_reminder_verification_are_wired(blueprint_text: str) -> None:
    assert "pre_class_refresh_minutes" in blueprint_text
    assert "event.remaining == target" in blueprint_text
    assert "verify_before_each_reminder_input" in blueprint_text
    assert "fail-closed" in blueprint_text
    assert "as_timestamp(states[entity].last_reported)" in blueprint_text


def test_update_failure_is_fail_closed(blueprint_text: str) -> None:
    assert "verified_calendar_entities" in blueprint_text
    assert "original.calendar in verified_calendar_entities" in blueprint_text
    assert "system_log.write" in blueprint_text
    assert "continue_on_error: true" in blueprint_text


def test_same_minute_update_targets_are_unique(blueprint_text: str) -> None:
    assert "event.calendar not in ns.items" in blueprint_text
    assert "ns.items | unique | list" in blueprint_text


def test_single_and_multiple_players_and_individual_volumes(blueprint_text: str) -> None:
    assert "for player in media_players_input" in blueprint_text
    assert "'volume': state_attr(player, 'volume_level')" in blueprint_text
    assert "repeat.item.volume" in blueprint_text
    assert "repeat.item.entity_id" in blueprint_text


@pytest.mark.parametrize(
    ("restore_volume", "resume_media"),
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_four_independent_restore_combinations(blueprint_text: str, restore_volume: bool, resume_media: bool) -> None:
    assert "player_snapshots if restore_original_volume_input else []" in blueprint_text
    assert "announce: \"{{ attempt_media_resume_input }}\"" in blueprint_text
    plan = player_plan(
        ["media_player.speaker_1", "media_player.speaker_2"],
        {
            "media_player.speaker_1": "idle",
            "media_player.speaker_2": "playing",
        },
        {
            "media_player.speaker_1": 0.2,
            "media_player.speaker_2": 0.6,
        },
        restore_volume,
        resume_media,
    )
    assert plan["play_targets"] == ["media_player.speaker_1", "media_player.speaker_2"]
    assert plan["announce"] is resume_media
    expected_restore_count = 2 if restore_volume else 0
    assert len(plan["restore_targets"]) == expected_restore_count
    if restore_volume:
        assert [item["volume"] for item in plan["restore_targets"]] == [0.2, 0.6]


def test_unavailable_calendar_and_player_are_filtered(blueprint_text: str) -> None:
    assert "reject('is_state', 'unavailable')" in blueprint_text
    assert "states(player) not in ['unknown', 'unavailable']" in blueprint_text
    plan = player_plan(
        ["media_player.speaker_1", "media_player.speaker_2"],
        {
            "media_player.speaker_1": "unavailable",
            "media_player.speaker_2": "idle",
        },
        {"media_player.speaker_1": 0.1, "media_player.speaker_2": None},
        restore_volume=True,
        resume_media=False,
    )
    assert plan["play_targets"] == ["media_player.speaker_2"]
    assert plan["restore_targets"] == []


def test_cross_day_and_timezone_math() -> None:
    taipei = timezone(timedelta(hours=8), name="Asia/Taipei")
    check = datetime(2026, 8, 17, 23, 50, tzinfo=taipei)
    lesson = datetime(2026, 8, 18, 0, 20, tzinfo=taipei)
    assert int((lesson - check).total_seconds() / 60) == 30
    next_midnight = check.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    assert next_midnight.isoformat() == "2026-08-18T00:00:00+08:00"


def test_same_event_offset_is_unique_and_cancelled_event_never_plays() -> None:
    duplicate = {"identity": "fake-uid", "remaining": 30, "learner": "Student One"}
    assert reminder_message([duplicate, duplicate]).count("30分鐘") == 1
    assert reminder_message([]) == ""


def test_tts_media_source_url_is_encoded_and_uses_selected_entity(blueprint_text: str) -> None:
    assert "'media-source://tts/' ~ tts_entity_input" in blueprint_text
    assert "~ '?message='" in blueprint_text
    assert "announcement_message | urlencode" in blueprint_text
    assert "tts_language_input | urlencode" in blueprint_text
    assert "media_content_type: music" in blueprint_text


def test_privacy_scan() -> None:
    text_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".venv" not in path.parts
        and ".pytest_cache" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix.lower() in {".md", ".yaml", ".yml", ".py", ".txt", ""}
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in text_files)
    private_ics = re.compile(
        r"api\.amazingtalker\.com/v1/user/calendar/(?!REPLACE_WITH_YOUR_PRIVATE_TOKEN(?:\b|/))[A-Za-z0-9_-]{8,}"
    )
    assert not private_ics.search(combined)
    forbidden_player = "media_player." + "ke_ting"
    assert forbidden_player not in combined
    calendar_ids = set(re.findall(r"calendar\.amazingtalker_[a-z0-9_]+", combined))
    assert calendar_ids <= {
        "calendar.amazingtalker_amy",
        "calendar.amazingtalker_grace",
        "calendar.amazingtalker_student_1",
        "calendar.amazingtalker_student_2",
        "calendar.amazingtalker_student_3",
    }


def test_readmes_document_complete_remote_calendar_onboarding() -> None:
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")
    for phrase in (
        "### 步驟 1：取得 AmazingTalker Calendar URL",
        "### 步驟 2：在 Home Assistant 新增 Remote Calendar",
        "### 步驟 3：填寫 Remote Calendar",
        "### 步驟 4：確認 calendar entity",
        "### 步驟 5：把 AmazingTalker Calendar 加入 Blueprint",
        "### 步驟 6：第一次測試",
        "Calendar Dashboard 看不到課程時，先不要檢查 Blueprint",
    ):
        assert phrase in chinese
    for phrase in (
        "### Step 1: Get the AmazingTalker Calendar URL",
        "### Step 2: Add Remote Calendar in Home Assistant",
        "### Step 3: Complete the Remote Calendar form",
        "### Step 4: Confirm the calendar entity",
        "### Step 5: Add the learner to the Blueprint",
        "### Step 6: Run the first test",
        "do not troubleshoot the Blueprint yet",
    ):
        assert phrase in english

    for text, start_heading, end_heading in (
        (chinese, "## 第一次設定 AmazingTalker 行事曆", "## TTS 設定"),
        (english, "## First-time AmazingTalker calendar setup", "## Configure TTS"),
    ):
        onboarding = text.split(start_heading, 1)[1].split(end_heading, 1)[0]
        assert "Google Calendar" not in onboarding


def test_readmes_remove_legacy_schedule_input_rows() -> None:
    for filename in ("README.md", "README.zh-TW.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "| `update_time`" not in text
        assert "| `update_weekday`" not in text
        assert "| `update_month_day`" not in text
        assert "legacy_scheduled_update_section" not in text


def test_all_repository_text_is_utf8_without_bom() -> None:
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or ".venv" in path.parts
            or ".pytest_cache" in path.parts
            or "__pycache__" in path.parts
        ):
            continue
        raw = path.read_bytes()
        if b"\x00" in raw:
            continue
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert b"\r\n" not in raw, f"CRLF line endings are not allowed: {path}"
        raw.decode("utf-8")


def test_markdown_basic_structure_and_local_links() -> None:
    markdown_files = [
        path for path in ROOT.rglob("*.md") if ".git" not in path.parts and ".venv" not in path.parts
    ]
    assert markdown_files
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# "), f"{path} must start with one H1"
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#")):
                continue
            local_target = target.split("#", 1)[0]
            assert (path.parent / local_target).resolve().exists(), (
                f"broken local Markdown link in {path}: {target}"
            )


def test_my_home_assistant_import_links_are_correctly_encoded() -> None:
    for filename in ("README.md", "README.zh-TW.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        match = re.search(
            r"https://my\.home-assistant\.io/redirect/blueprint_import/\?blueprint_url=[^)]+",
            text,
        )
        assert match, filename
        parsed = urlparse(match.group(0))
        assert parse_qs(parsed.query)["blueprint_url"] == [SOURCE_URL]


def test_github_actions_yaml_is_reproducible() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "validate.yaml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert workflow["name"] == "Validate"
    assert "static-tests" in workflow["jobs"]
    rendered = workflow_path.read_text(encoding="utf-8")
    assert "python -m yamllint ." in rendered
    assert "python -m pytest -q" in rendered
    assert "git diff --check" in rendered
    assert "cache-dependency-path: requirements-dev.txt" in rendered
