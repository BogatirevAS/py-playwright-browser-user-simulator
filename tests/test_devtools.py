import pytest

from pbus import BrowserNameEnum, PlaywrightBrowserUserSimulator


class TestDevTools:
    pytestmark = [pytest.mark.integration, pytest.mark.slow]

    async def test_devtools_flag_not_passed_by_default(
            self, wrapper_config, base_settings, static_site
    ):
        settings = base_settings.model_copy(update={
            "browser_name": BrowserNameEnum.CHROMIUM,
            "devtools": False,
            "headless": False,
        })

        assert settings.args is None

        async with PlaywrightBrowserUserSimulator(
                wrapper_config, settings,
                headless=False, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)

            cdp = await ctx.impl_obj.new_cdp_session(page)
            try:
                resp = await cdp.send("Browser.getBrowserCommandLine")
                browser_args = resp["arguments"]
            finally:
                await cdp.detach()

        assert "--auto-open-devtools-for-tabs" not in browser_args, (
            f"Flag DevTools set in browser. "
            f"Args: {browser_args}"
        )

    async def test_devtools_arg_is_passed_to_browser(
            self, wrapper_config, base_settings, static_site
    ):
        settings = base_settings.model_copy(update={
            "browser_name": BrowserNameEnum.CHROMIUM,
            "devtools": True,
            "headless": False,
        })

        assert settings.args == ["--auto-open-devtools-for-tabs"]

        async with PlaywrightBrowserUserSimulator(
                wrapper_config, settings,
                headless=False, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)

            cdp = await ctx.impl_obj.new_cdp_session(page)
            try:
                resp = await cdp.send("Browser.getBrowserCommandLine")
                browser_args = resp["arguments"]
            finally:
                await cdp.detach()

        assert "--auto-open-devtools-for-tabs" in browser_args, (
            f"Flag DevTools no set in browser. Args: {browser_args}"
        )
        assert "--headless" not in browser_args, (
            f"Browser in headless, DevTools no opened. "
            f"Args: {browser_args}"
        )

    async def test_devtools_flag_not_passed_for_firefox(
            self, wrapper_config, base_settings, static_site
    ):
        settings = base_settings.model_copy(update={
            "browser_name": BrowserNameEnum.FIREFOX,
            "devtools": True,
            "headless": True,
        })

        assert settings.args is None

        async with PlaywrightBrowserUserSimulator(
                wrapper_config, settings,
                headless=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            assert await page.title() == "pbus test"
