import os
from pathlib import Path
from playwright.async_api import ViewportSize, ProxySettings
from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal, TypedDict, Sequence

from logger import LogLevel, SettingsCreateOrUpdateMixin
from pbus.components.enums import BrowserNameEnum


class PbusSettingsKwargs(TypedDict, total=False):
    tmp_path: Path
    browser_name: BrowserNameEnum
    persistent: bool
    seconds_to_close: int
    retries: int
    stealth: bool
    include_storage_state: bool
    method_log_level: LogLevel
    default_timeout: float
    save_as_move: bool
    timeout: float
    headless: bool
    devtools: bool
    proxy: Optional[ProxySettings]
    downloads_path: Optional[Path]
    slow_mo: int
    viewport: ViewportSize
    ignore_https_errors: bool
    user_agent: Optional[str]
    locale: str
    color_scheme: Literal["dark", "light", "no-preference", "null"]
    browser_args: Optional[Sequence[str]]


class PbusSettings(BaseSettings, SettingsCreateOrUpdateMixin):
    model_config = SettingsConfigDict(env_prefix="PBUS_", extra="ignore", env_ignore_empty=True)

    tmp_path: Path = Path("tmp")
    browser_name: BrowserNameEnum = BrowserNameEnum.FIREFOX
    persistent: bool = False
    seconds_to_close: int = 3
    retries: int = 1
    stealth: bool = False
    include_storage_state: bool = False
    method_log_level: LogLevel = LogLevel.DEBUG
    default_timeout: float = 30000
    save_as_move: bool = False

    @computed_field
    @property
    def user_data_dir(self) -> Path:
        return self.tmp_path / "user_data" / self.browser_name.value

    timeout: float = 30000
    headless: bool = True
    devtools: bool = False
    proxy: Optional[ProxySettings] = None
    downloads_path: Optional[Path] = None

    @model_validator(mode='after')
    def _set_downloads_path_default(self):
        if self.downloads_path is None:
            self.downloads_path = self.tmp_path / "downloads"
        return self

    slow_mo: int = 1000
    viewport: ViewportSize = {"width": 1280, "height": 960}
    ignore_https_errors: bool = True
    user_agent: Optional[str] = None
    locale: str = "en-EN"
    color_scheme: Literal["dark", "light", "no-preference", "null"] = "dark"

    @computed_field
    @property
    def storage_state_path(self) -> Path:
        return self.tmp_path / ".auth" / self.browser_name.value / "state.json"

    @computed_field
    @property
    def storage_state(self) -> Optional[Path]:
        if self.include_storage_state and os.path.exists(self.storage_state_path):
            return self.storage_state_path
        return None

    browser_args: Optional[Sequence[str]] = None

    @computed_field
    @property
    def args(self) -> Sequence[str]:
        args = []
        if self.browser_args:
            args.extend(self.browser_args)
        if self.devtools and self.browser_name == BrowserNameEnum.CHROMIUM:
            args.extend(["--auto-open-devtools-for-tabs"])
        return args or None
