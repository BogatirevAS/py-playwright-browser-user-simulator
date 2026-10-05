from __future__ import annotations

import inspect

import pytest

from pbus import PlaywrightBrowserUserSimulator, PbusPage

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestWrapperTypes:
    async def test_page_is_custom_wrapper(self, wrapper_config, base_settings):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            assert type(page).__name__ == "PbusPage"

    async def test_locator_is_custom_wrapper(self, wrapper_config, base_settings):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            loc = page.locator("div")
            assert type(loc).__name__ == "PbusLocator"

    async def test_locator_all_returns_wrapped_list(
        self, wrapper_config, base_settings, static_site
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            items = await page.locator("div.col").all()
            assert len(items) == 3
            for item in items:
                assert type(item).__name__ == "PbusLocator"


class TestTransparentWrapping:
    async def test_signatures_are_preserved(self, wrapper_config, base_settings):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()

            sig = inspect.signature(page.goto)
            for name in ("url", "wait_until", "timeout", "referer"):
                assert name in sig.parameters

    async def test_chained_calls_still_wrap(self, wrapper_config, base_settings, static_site):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            loc = page.locator("body").locator("div.col").nth(0)
            assert type(loc).__name__ == "PbusLocator"

    async def test_custom_method_on_wrapper_is_available(
        self, wrapper_config, base_settings, static_site
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            assert hasattr(page, "wait_to_close")


class TestWrapperConfigIsolation:
    async def test_different_wrapper_configs_produce_different_types(
        self, base_settings
    ):
        from pbus import PbusWrapperConfig

        class _AltPageClass(PbusPage):
            pass

        cfg_a = PbusWrapperConfig(page_class=_AltPageClass)
        cfg_b = PbusWrapperConfig()

        async with PlaywrightBrowserUserSimulator(
            cfg_a, base_settings, headless=True, seconds_to_close=0
        ) as ctx_a:
            page_a = await ctx_a.new_page()

        async with PlaywrightBrowserUserSimulator(
            cfg_b, base_settings, headless=True, seconds_to_close=0
        ) as ctx_b:
            page_b = await ctx_b.new_page()

        assert type(page_a).__name__ != type(page_b).__name__
