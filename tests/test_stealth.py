from __future__ import annotations

import pytest

from pbus import PlaywrightBrowserUserSimulator


pytestmark = [pytest.mark.integration, pytest.mark.slow]


async def _webdriver_flag(page) -> object:
    return await page.evaluate("() => navigator.webdriver")


class TestStealthMode:
    async def test_stealth_disabled_leaves_webdriver_flag(
        self, wrapper_config, base_settings
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings,
            headless=True, stealth=False, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto("about:blank")
            assert await _webdriver_flag(page) is True

    async def test_stealth_enabled_hides_webdriver_flag(
        self, wrapper_config, base_settings
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings,
            headless=True, stealth=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto("about:blank")
            value = await _webdriver_flag(page)
            assert value in (None, False)

    async def test_stealth_applies_to_new_pages(
        self, wrapper_config, base_settings
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings,
            headless=True, stealth=True, seconds_to_close=0,
        ) as ctx:
            page1 = await ctx.new_page()
            page2 = await ctx.new_page()
            for p in (page1, page2):
                await p.goto("about:blank")
                assert await _webdriver_flag(p) in (None, False)

    async def test_stealth_does_not_break_navigation(
        self, wrapper_config, base_settings, static_site
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings,
            headless=True, stealth=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            assert "pbus test" in (await page.title())
