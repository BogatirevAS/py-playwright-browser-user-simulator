from typing import Optional, TYPE_CHECKING, Unpack
from playwright.async_api import Playwright, Browser, BrowserType, async_playwright
from playwright_stealth import Stealth

from logger import LoggerMixin
from pbus.settings.base import PbusSettings, PbusSettingsKwargs
from pbus.settings.wrapper import PbusWrapperRegistry
if TYPE_CHECKING:
    from pbus.settings.wrapper import PbusWrapperConfig
    from pbus.classes.browser_context import PbusBrowserContext


class PlaywrightBrowserUserSimulator(LoggerMixin):
    def __init__(self, wrapper_config: Optional["PbusWrapperConfig"] = None,
                 settings: Optional[PbusSettings] = None,
                 **kwargs: Unpack[PbusSettingsKwargs]):
        self.logger.debug("Create PBUS")
        self._wrapper_config = wrapper_config or PbusWrapperRegistry.get_config()
        self._settings = PbusSettings.create_or_update(settings, **kwargs)
        self._playwright: Optional[Playwright] = None
        self._browser_type: Optional[BrowserType] = None
        self._browser: Optional[Browser] = None
        self._browser_context: Optional["PbusBrowserContext"] = None
        self._stealth = Stealth() if self.settings.stealth else None

    @property
    def wrapper_config(self) -> "PbusWrapperConfig":
        return self._wrapper_config

    @property
    def settings(self) -> PbusSettings:
        return self._settings

    @property
    def playwright(self) -> Playwright:
        return self._playwright

    @property
    def browser_type(self) -> BrowserType:
        return self._browser_type

    @property
    def browser(self) -> Browser:
        return self._browser

    @property
    def browser_context(self) -> "PbusBrowserContext":
        return self._browser_context

    @property
    def browser_name(self) -> str:
        return self.settings.browser_name.value

    @property
    def stealth(self) -> Stealth:
        return self._stealth

    @property
    def browser_kwargs(self):
        included = [
            "timeout",
            "headless",
            "proxy",
            "downloads_path",
            "slow_mo",
            "args",
        ]
        return {k: getattr(self.settings, k) for k in included}

    @property
    def context_kwargs(self):
        included = [
            "viewport",
            "ignore_https_errors",
            "user_agent",
            "locale",
            "color_scheme",
            "storage_state",
        ]
        return {k: getattr(self.settings, k) for k in included}

    @property
    def browser_context_kwargs(self):
        included = [
            "user_data_dir",
            "timeout",
            "headless",
            "proxy",
            "downloads_path",
            "slow_mo",
            "viewport",
            "ignore_https_errors",
            "user_agent",
            "locale",
            "color_scheme",
            "args",
        ]
        return {k: getattr(self.settings, k) for k in included}

    async def _launch_persistent_browser_context(self):
        kwargs = self.browser_context_kwargs
        self.logger.debug(f"{self.browser_name}.launch_persistent_context: {kwargs}")
        return await self.browser_type.launch_persistent_context(**kwargs)

    async def _launch_browser_with_context(self):
        kwargs = self.browser_kwargs
        self.logger.debug(f"{self.browser_name}.launch: {kwargs}")
        self._browser = await self.browser_type.launch(**kwargs)
        kwargs = self.context_kwargs
        self.logger.debug(f"browser.new_context: {kwargs}")
        return await self.browser.new_context(**kwargs)

    async def _launch_browser_context(self) -> "PbusBrowserContext":
        if self.settings.persistent:
            browser_context = await self._launch_persistent_browser_context()
        else:
            browser_context = await self._launch_browser_with_context()
        self._browser_context = self.wrapper_config.create_wrapper(self, browser_context)
        if self.stealth:
            await self.stealth.apply_stealth_async(self.browser_context)
        self.logger.debug(f"browser_context.set_default_timeout({self.settings.default_timeout}")
        self.browser_context.set_default_timeout(self.settings.default_timeout)
        return self.browser_context

    async def __aenter__(self) -> "PbusBrowserContext":
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self) -> "PbusBrowserContext":
        self._playwright = await async_playwright().start()
        self._browser_type = getattr(self.playwright, self.browser_name)
        return await self._launch_browser_context()

    async def stop(self):
        if self.browser_context:
            await self.browser_context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
