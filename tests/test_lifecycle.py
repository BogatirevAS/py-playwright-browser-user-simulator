from __future__ import annotations

import asyncio
import time

import pytest

from pbus import PlaywrightBrowserUserSimulator


pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestCloseDelay:
    async def test_seconds_to_close_delays_exit(self, wrapper_config, base_settings):
        settings = base_settings.model_copy(update={"seconds_to_close": 1})

        start = time.monotonic()
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings, headless=True, seconds_to_close=1,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto("about:blank")
        elapsed = time.monotonic() - start

        assert elapsed >= 0.9

    async def test_seconds_to_close_zero_exits_fast(
        self, wrapper_config, base_settings
    ):
        start = time.monotonic()
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0,
        ) as ctx:
            await ctx.new_page()
        assert time.monotonic() - start < 5


class TestConcurrentUsage:
    async def test_two_simulators_in_parallel(
        self, wrapper_config, base_settings, static_site
    ):
        async def run():
            async with PlaywrightBrowserUserSimulator(
                wrapper_config, base_settings, headless=True, seconds_to_close=0
            ) as ctx:
                page = await ctx.new_page()
                await page.goto(static_site)
                return await page.title()

        results = await asyncio.gather(run(), run())
        assert results == ["pbus test", "pbus test"]
