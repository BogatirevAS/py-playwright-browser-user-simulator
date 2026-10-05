from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from pbus import PbusSettings, BrowserNameEnum
from logger import LogLevel


FIELDS = set(PbusSettings.model_fields)


@pytest.fixture(autouse=True)
def _clean_pbus_env(monkeypatch: pytest.MonkeyPatch):
    for k in list(os.environ):
        if k.startswith("PBUS_"):
            monkeypatch.delenv(k, raising=False)


def test_settings_defaults():
    s = PbusSettings(_env_file=None)
    assert s.model_dump(include=FIELDS) == {
        "tmp_path": Path("tmp"),
        "browser_name": BrowserNameEnum.FIREFOX,
        "persistent": False,
        "seconds_to_close": 3,
        "retries": 1,
        "stealth": False,
        "include_storage_state": False,
        "method_log_level": LogLevel.DEBUG,
        "default_timeout": 30000.0,
        "save_as_move": False,
        "timeout": 30000.0,
        "headless": True,
        "devtools": False,
        "proxy": None,
        "downloads_path": Path("tmp") / "downloads",
        "slow_mo": 1000,
        "viewport": {"width": 1280, "height": 960},
        "ignore_https_errors": True,
        "user_agent": None,
        "locale": "en-EN",
        "color_scheme": "dark",
        "browser_args": None,
    }


@pytest.mark.parametrize("env_name,value,attr,expected", [
    ("PBUS_TMP_PATH", "custom/path", "tmp_path", Path("custom/path")),
    ("PBUS_BROWSER_NAME", "chromium", "browser_name", BrowserNameEnum.CHROMIUM),
    ("PBUS_PERSISTENT", "true", "persistent", True),
    ("PBUS_SECONDS_TO_CLOSE", "10", "seconds_to_close", 10),
    ("PBUS_RETRIES", "5", "retries", 5),
    ("PBUS_STEALTH", "true", "stealth", True),
    ("PBUS_INCLUDE_STORAGE_STATE", "true", "include_storage_state", True),
    ("PBUS_METHOD_LOG_LEVEL", "warning", "method_log_level", LogLevel.WARNING),
    ("PBUS_DEFAULT_TIMEOUT", "15000", "default_timeout", 15000.0),
    ("PBUS_SAVE_AS_MOVE", "true", "save_as_move", True),
    ("PBUS_TIMEOUT", "5000", "timeout", 5000.0),
    ("PBUS_HEADLESS", "false", "headless", False),
    ("PBUS_DEVTOOLS", "true", "devtools", True),
    ("PBUS_SLOW_MO", "0", "slow_mo", 0),
    ("PBUS_IGNORE_HTTPS_ERRORS", "false", "ignore_https_errors", False),
    ("PBUS_USER_AGENT", "pbus-test", "user_agent", "pbus-test"),
    ("PBUS_LOCALE", "ru-RU", "locale", "ru-RU"),
    ("PBUS_COLOR_SCHEME", "light", "color_scheme", "light"),
    ("PBUS_DOWNLOADS_PATH", "dl", "downloads_path", Path("dl")),
    ("PBUS_VIEWPORT", '{"width":800,"height":600}', "viewport", {"width": 800, "height": 600}),
    ("PBUS_BROWSER_ARGS", '["--disable-gpu","--no-sandbox"]', "browser_args", ["--disable-gpu", "--no-sandbox"]),
])
def test_settings_each_env_var(monkeypatch, env_name, value, attr, expected):
    monkeypatch.setenv(env_name, value)
    s = PbusSettings(_env_file=None)
    assert getattr(s, attr) == expected


def test_env_without_prefix_is_ignored(monkeypatch):
    monkeypatch.setenv("HEADLESS", "false")
    monkeypatch.setenv("SECONDS_TO_CLOSE", "99")
    s = PbusSettings(_env_file=None)
    assert s.headless is True
    assert s.seconds_to_close == 3


def test_env_empty_is_ignored(monkeypatch):
    monkeypatch.setenv("PBUS_HEADLESS", "")
    monkeypatch.setenv("PBUS_LOCALE", "")
    s = PbusSettings(_env_file=None)
    assert s.headless is True
    assert s.locale == "en-EN"


def test_unknown_env_with_prefix_is_ignored(monkeypatch):
    monkeypatch.setenv("PBUS_UNKNOWN_FIELD", "whatever")
    s = PbusSettings(_env_file=None)
    assert s.seconds_to_close == 3


def test_dotenv_is_loaded(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "PBUS_HEADLESS=false\n"
        "PBUS_SECONDS_TO_CLOSE=7\n"
        "PBUS_BROWSER_NAME=chromium\n",
        encoding="utf-8",
    )
    s = PbusSettings(_env_file=env_file)
    assert s.headless is False
    assert s.seconds_to_close == 7
    assert s.browser_name == BrowserNameEnum.CHROMIUM


@pytest.mark.parametrize("field,value", [
    ("seconds_to_close", "not-a-number"),
    ("retries", "abc"),
    ("persistent", "maybe"),
    ("browser_name", "netscape"),
    ("method_log_level", "verbose"),
    ("color_scheme", "sepia"),
])
def test_settings_strict_types(monkeypatch, field, value):
    monkeypatch.setenv(f"PBUS_{field.upper()}", value)
    with pytest.raises(ValidationError):
        PbusSettings(_env_file=None)


class TestComputedUserDataDir:
    def test_default(self):
        s = PbusSettings(_env_file=None)
        assert s.user_data_dir == Path("tmp") / "user_data" / "firefox"

    def test_depends_on_browser(self):
        s = PbusSettings(browser_name=BrowserNameEnum.CHROMIUM, _env_file=None)
        assert s.user_data_dir == Path("tmp") / "user_data" / "chromium"

    def test_depends_on_tmp_path(self, tmp_path: Path):
        s = PbusSettings(tmp_path=tmp_path, _env_file=None)
        assert s.user_data_dir == tmp_path / "user_data" / "firefox"

    def test_reflected_in_model_dump(self):
        s = PbusSettings(_env_file=None)
        assert s.model_dump()["user_data_dir"] == Path("tmp") / "user_data" / "firefox"


class TestComputedStorageStatePath:
    def test_layout(self):
        s = PbusSettings(_env_file=None)
        assert s.storage_state_path == Path("tmp") / ".auth" / "firefox" / "state.json"

    def test_depends_on_browser(self):
        s = PbusSettings(browser_name=BrowserNameEnum.CHROMIUM, _env_file=None)
        assert s.storage_state_path == Path("tmp") / ".auth" / "chromium" / "state.json"


class TestComputedStorageState:
    def test_none_when_flag_disabled_even_if_file_exists(self, tmp_path: Path):
        s = PbusSettings(tmp_path=tmp_path, include_storage_state=False, _env_file=None)
        s.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        s.storage_state_path.write_text("{}", encoding="utf-8")
        assert s.storage_state is None

    def test_none_when_flag_enabled_but_file_missing(self, tmp_path: Path):
        s = PbusSettings(tmp_path=tmp_path, include_storage_state=True, _env_file=None)
        assert not s.storage_state_path.exists()
        assert s.storage_state is None

    def test_returns_path_when_both_present(self, tmp_path: Path):
        s = PbusSettings(tmp_path=tmp_path, include_storage_state=True, _env_file=None)
        s.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        s.storage_state_path.write_text("{}", encoding="utf-8")
        assert s.storage_state == s.storage_state_path


class TestDownloadsPathValidator:
    def test_default_is_filled_from_tmp_path(self):
        s = PbusSettings(_env_file=None)
        assert s.downloads_path == Path("tmp") / "downloads"

    def test_explicit_value_is_kept(self):
        s = PbusSettings(downloads_path=Path("my/dl"), _env_file=None)
        assert s.downloads_path == Path("my/dl")

    def test_follows_tmp_path(self, tmp_path: Path):
        s = PbusSettings(tmp_path=tmp_path, _env_file=None)
        assert s.downloads_path == tmp_path / "downloads"


class TestArgsComputed:
    def test_empty_by_default(self):
        s = PbusSettings(_env_file=None)
        assert s.args is None

    def test_devtools_chromium_adds_flag(self):
        s = PbusSettings(
            browser_name=BrowserNameEnum.CHROMIUM,
            devtools=True,
            _env_file=None,
        )
        assert s.args == ["--auto-open-devtools-for-tabs"]

    def test_devtools_firefox_is_noop(self):
        s = PbusSettings(
            browser_name=BrowserNameEnum.FIREFOX,
            devtools=True,
            _env_file=None,
        )
        assert s.args is None

    def test_user_args_are_kept(self):
        s = PbusSettings(browser_args=["--foo", "--bar"], _env_file=None)
        assert s.args == ["--foo", "--bar"]

    def test_user_args_and_devtools_are_merged(self):
        s = PbusSettings(
            browser_name=BrowserNameEnum.CHROMIUM,
            browser_args=["--foo"],
            devtools=True,
            _env_file=None,
        )
        assert list(s.args) == ["--foo", "--auto-open-devtools-for-tabs"]


class TestSerialization:
    def test_model_dump_contains_flat_fields(self):
        s = PbusSettings(_env_file=None)
        dumped = s.model_dump()
        for key in FIELDS:
            assert key in dumped, f"{key} no in model_dump()"

    def test_model_dump_contains_computed_fields(self):
        s = PbusSettings(_env_file=None)
        dumped = s.model_dump()
        for key in ("user_data_dir", "storage_state_path", "storage_state", "args"):
            assert key in dumped, f"{key} no in model_dump()"

    def test_json_roundtrip(self):
        s = PbusSettings(_env_file=None)
        data = s.model_dump(mode="json")
        assert data["tmp_path"] == "tmp"
        assert data["browser_name"] == "firefox"
        assert data["downloads_path"].endswith("downloads")

    def test_json_dumps_does_not_raise(self):
        import json
        s = PbusSettings(_env_file=None)
        json.dumps(s.model_dump(mode="json"))
