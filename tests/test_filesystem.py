from __future__ import annotations

import json
from pathlib import Path

import pytest

from pbus import PlaywrightBrowserUserSimulator


@pytest.fixture()
def settings(base_settings, tmp_path: Path):
    return base_settings.model_copy(update={"tmp_path": tmp_path})


class TestScreenshots:
    pytestmark = [pytest.mark.integration, pytest.mark.slow]

    async def test_screenshot_saves_to_given_path(
        self, wrapper_config, settings, tmp_path: Path, static_site
    ):
        target = tmp_path / "screens" / "home.png"
        target.parent.mkdir(parents=True, exist_ok=True)

        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            await page.screenshot(path=target)

        assert target.exists()
        assert target.stat().st_size > 0
        assert target.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_screenshot_without_path_returns_bytes(
        self, wrapper_config, settings, static_site
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            data = await page.screenshot()

        assert isinstance(data, bytes)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_full_page_screenshot_differs_from_viewport(
        self, wrapper_config, settings, tmp_path: Path, static_site
    ):
        viewport = tmp_path / "viewport.png"
        full = tmp_path / "full.png"

        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            await page.screenshot(path=viewport)
            await page.screenshot(path=full, full_page=True)

        assert viewport.exists() and full.exists()
        assert full.stat().st_size >= viewport.stat().st_size


# ---------------------------------------------------------------- downloads

class TestDownloads:
    pytestmark = [pytest.mark.integration, pytest.mark.slow]

    async def test_download_saves_to_given_path(
        self, wrapper_config, settings, tmp_path: Path, static_site
    ):
        target = tmp_path / "downloads" / "file.bin"
        target.parent.mkdir(parents=True, exist_ok=True)

        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)

            async with page.expect_download() as dl_info:
                await page.click("#dl")
            download = await dl_info.value
            await download.save_as(target)

        assert target.exists()
        assert target.stat().st_size > 0
        assert target.read_bytes().startswith(b"\x00\x01\x02")


class TestStorageStateComputed:

    pytestmark = pytest.mark.unit

    def test_storage_state_path_layout(self, settings):
        expected = settings.tmp_path / ".auth" / settings.browser_name.value / "state.json"
        assert settings.storage_state_path == expected

    def test_computed_is_none_when_file_missing(self, settings):
        s = settings.model_copy(update={"include_storage_state": True})
        assert not s.storage_state_path.exists()
        assert s.storage_state is None

    def test_computed_returns_path_when_file_present(self, settings):
        s = settings.model_copy(update={"include_storage_state": True})
        s.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        s.storage_state_path.write_text("{}", encoding="utf-8")
        assert s.storage_state == s.storage_state_path

    def test_computed_is_none_when_flag_disabled_even_if_file_exists(self, settings):
        s = settings.model_copy(update={"include_storage_state": False})
        s.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        s.storage_state_path.write_text("{}", encoding="utf-8")
        assert s.storage_state is None


class TestStorageStateRuntime:
    pytestmark = [pytest.mark.integration, pytest.mark.slow]

    async def test_state_is_saved_when_enabled(
        self, wrapper_config, settings, static_site
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
            include_storage_state=True,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            await ctx.add_cookies([{
                "name": "a", "value": "b",
                "url": static_site,
                "expires": 4102444800,
            }])
            await ctx.storage_state()

        state_path = settings.storage_state_path
        assert state_path.exists(), f"state no saved in {state_path}"

        data = json.loads(state_path.read_text(encoding="utf-8"))
        names = [c["name"] for c in data.get("cookies", [])]
        assert "a" in names

    async def test_state_is_reused_on_next_launch(
        self, wrapper_config, settings, static_site
    ):
        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
            include_storage_state=True,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            await ctx.add_cookies([{
                "name": "persisted", "value": "1",
                "url": static_site,
                "expires": 4102444800,
            }])
            await ctx.storage_state()

        assert settings.storage_state_path.exists()

        async with PlaywrightBrowserUserSimulator(
            wrapper_config, settings,
            headless=True, seconds_to_close=0,
            include_storage_state=True,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            cookies = await ctx.cookies(static_site)
            names = [c["name"] for c in cookies]
            assert "persisted" in names, f"cookies on second run: {names}"

    async def test_disabled_flag_does_not_load_existing_state(
        self, wrapper_config, settings, static_site
    ):
        settings.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        settings.storage_state_path.write_text(
            json.dumps({
                "cookies": [{
                    "name": "leaked", "value": "1",
                    "domain": "127.0.0.1", "path": "/",
                    "expires": 4102444800,
                    "httpOnly": False, "secure": False, "sameSite": "Lax",
                }],
                "origins": [],
            }),
            encoding="utf-8",
        )

        async with PlaywrightBrowserUserSimulator(
            wrapper_config,
            settings.model_copy(update={"include_storage_state": False}),
            headless=True, seconds_to_close=0,
            include_storage_state=False,
        ) as ctx:
            page = await ctx.new_page()
            await page.goto(static_site)
            cookies = await ctx.cookies(static_site)
            names = [c["name"] for c in cookies]
            assert "leaked" not in names
