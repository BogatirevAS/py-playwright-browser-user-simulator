from __future__ import annotations

import asyncio
import pytest

from pbus import PlaywrightBrowserUserSimulator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestRegularLaunch:
    async def test_context_manager_yields_context(
        self, wrapper_config, base_settings
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config,
            base_settings,
            headless=True,
            stealth=False,
            include_storage_state=False,
            seconds_to_close=0,
            persistent=False,
        ) as ctx:
            assert ctx is not None
            page = await ctx.new_page()
            await page.goto("about:blank")
            assert await page.title() == ""

    async def test_pages_are_wrapped(self, wrapper_config, base_settings):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            assert type(page).__name__ == "PbusPage"
            assert hasattr(page, "goto")
            assert hasattr(page, "locator")

    async def test_browser_is_closed_after_exit(self, wrapper_config, base_settings):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings, headless=True, seconds_to_close=0
        ) as ctx:
            page = await ctx.new_page()
            await page.goto("about:blank")
            browser = ctx.browser

        assert page.is_closed()


class TestPersistentLaunch:
    async def test_persistent_mode_reuses_user_data_dir(
        self, wrapper_config, base_settings, tmp_path
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config,
            base_settings,
            headless=True,
            seconds_to_close=0,
            persistent=True,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto("about:blank")

        assert base_settings.user_data_dir.exists()

    async def test_persistent_mode_keeps_cookies_between_runs(
            self, wrapper_config, base_settings, tmp_path, static_site
    ):
        settings = base_settings.model_copy(update={
            "tmp_path": tmp_path,
            "persistent": True,
        })

        profile = settings.user_data_dir
        assert profile.parent.parent == tmp_path

        async with PlaywrightBrowserUserSimulator(
                wrapper_config, settings, headless=True,
                seconds_to_close=2, persistent=True,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            await ctx.add_cookies([{
                "name": "pbus", "value": "1",
                "url": static_site,
                "expires": 4102444800,
            }])
            got = await ctx.cookies(static_site)
            assert any(c["name"] == "pbus" for c in got)

        await asyncio.sleep(1.0)

        assert profile.exists(), f"no profile: {profile}"
        cookies_db = profile / "cookies.sqlite"
        assert cookies_db.exists(), (
            f"cookies.sqlite not found in {profile}\n"
            f"content: {[p.name for p in profile.rglob('*')] if profile.exists() else 'no folders'}"
        )

        async with PlaywrightBrowserUserSimulator(
                wrapper_config, settings, headless=True,
                seconds_to_close=2, persistent=True,
        ) as ctx:
            await (await ctx.new_page()).goto(static_site)
            cookies = await ctx.cookies(static_site)
            names = [c["name"] for c in cookies]
            assert "pbus" in names, f"cookies on second run: {names}"


class TestLaunchErrors:
    async def test_exception_inside_block_still_closes_browser(
        self, wrapper_config, base_settings
    ):
        page_ref = {}

        with pytest.raises(RuntimeError, match="boom"):
            async with PlaywrightBrowserUserSimulator(
                wrapper_config, base_settings, headless=True, seconds_to_close=0
            ) as ctx:
                page = await ctx.new_page()
                page_ref["page"] = page
                raise RuntimeError("boom")

        assert page_ref["page"].is_closed()


class TestHeadlessFlag:
    @pytest.mark.parametrize("headless", [True, False])
    async def test_headless_launch_works(
        self, wrapper_config, base_settings, headless
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, base_settings,
            headless=headless, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto("about:blank")
