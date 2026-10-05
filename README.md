# Playwright Browser User Simulator

> `pbus` is an asynchronous wrapper around Playwright that eliminates the boilerplate of
> browser initialization, adds stealth mode and file system management, and allows
> you to extend Playwright's behavior with your own custom wrappers.

-----

## Table of Contents

- [Installation](#installation)
- [Environment](#environment)
- [Examples](#examples)

## About

`pbus` was created for cases where a standard Playwright launch turns into a
verbose ritual: initialize `playwright`, start `browser`, create `context`,
remember about `storage_state`, don't forget to close everything behind you.
All of this is replaced by a single async context manager:

```python
async with PlaywrightBrowserUserSimulator(
    CustomPbusWrapperConfig(),
    CustomPbusSettings(),
    headless=False,
    stealth=True,
    include_storage_state=True,
    seconds_to_close=10,
    persistent=True,
) as browser_context:
    page: CustomPbusPage = await browser_context.new_page()
```

Under the hood `pbus` brings up Playwright, the browser and the context itself,
applies settings from environment variables and shuts everything down correctly
on your behalf.

## Features

- **Single entry point.** One `async with` — and you have a ready `BrowserContext`
  in either regular or persistent mode. No more manually coordinating the
  lifecycle of `playwright` → `browser` → `context`.

- **Environment-driven settings.** Configuration is read via `pydantic-settings`
  with support for `.env` files, environment variable prefixes and strict typing.

- **Stealth mode out of the box.** Enabled with `stealth=True` — the package
  applies `playwright-stealth` to the context and pages on its own.

- **File system management.** Saving files (screenshots, downloads, storage
  state, etc.) is driven by settings; save methods can be customised for your
  project's needs.

- **Custom wrappers.** Users can write their own wrapper classes over
  `BrowserContext`, `Page`, `Locator`, `Download` and modify base Playwright
  behaviour through decorators, mixins and metaclasses.

- **Transparent wrapping.** Wrappers preserve the original signatures and
  parameters of Playwright classes and methods — behaviour stays predictable,
  autocompletion and types keep working.

- **Modification components.** A set of ready-to-use components (decorators,
  mixins, enums, exceptions) makes extending wrappers easy without rewriting
  the base logic.

- **Async only.** The package supports only async Playwright. Synchronous and
  asynchronous Playwright generate incompatible classes, and supporting both
  would mean effectively maintaining two libraries. Async is chosen as the
  preferred scenario for real automation tasks.

## Installation

- console
```console
pip install git+https://github.com/BogatirevAS/py-playwright-browser-user-simulator.git@master
```
```console
pip install git+https://github.com/BogatirevAS/py-playwright-browser-user-simulator.git@0.1.0
```

- requirements.txt
```requirements
pbus @ git+https://github.com/BogatirevAS/py-playwright-browser-user-simulator.git@master
```
```requirements
pbus @ git+https://github.com/BogatirevAS/py-playwright-browser-user-simulator.git@0.1.0
```

## Environment
.env
```dotenv
PBUS_TMP_PATH=tmp
PBUS_BROWSER_NAME=firefox
PBUS_PERSISTENT=false
PBUS_SECONDS_TO_CLOSE=3
PBUS_RETRIES=1
PBUS_STEALTH=false
PBUS_INCLUDE_STORAGE_STATE=false
PBUS_METHOD_LOG_LEVEL=DEBUG
PBUS_DEFAULT_TIMEOUT=30000
PBUS_SAVE_AS_MOVE=false
PBUS_TIMEOUT=30000
PBUS_HEADLESS=true
PBUS_SLOW_MO=1000
PBUS_DOWNLOADS_PATH=
PBUS_PROXY=
PBUS_VIEWPORT={"width": 1280, "height": 960}
PBUS_IGNORE_HTTPS_ERRORS=true
PBUS_USER_AGENT=
PBUS_LOCALE=en-EN
PBUS_COLOR_SCHEME=dark
PBUS_DEVTOOLS=false
PBUS_BROWSER_ARGS=
```

## Examples
1. Quick start
    ```python
    async def test_example1():
        from pathlib import Path
        from pbus import PlaywrightBrowserUserSimulator, BrowserNameEnum, PbusPage
    
        async with PlaywrightBrowserUserSimulator(
                tmp_path=Path("tmp"),
                browser_name=BrowserNameEnum.CHROMIUM,
                headless=False,
                stealth=True,
                include_storage_state=True,
                seconds_to_close=1,
        ) as browser_context:
            page: PbusPage = await browser_context.new_page()
            await page.goto("http://www.playwright.com/")
            await page.wait_to_close()
    ```
2. Custom setup
    ```python
    async def test_example2():
        from pbus import PlaywrightBrowserUserSimulator, CustomPbusSettings, CustomPbusWrapperConfig, CustomPbusPage
    
        async with PlaywrightBrowserUserSimulator(
            CustomPbusWrapperConfig(),
            CustomPbusSettings(),
            seconds_to_close=1,
        ) as browser_context:
            page: CustomPbusPage = await browser_context.new_page()
            await page.goto("http://www.playwright.com/")
            await page.wait_to_close()
    ```
3. Your custom setup
    ```python
    async def test_example3():
        from pbus import PlaywrightBrowserUserSimulator, PbusPage, PbusLocator, PbusSettings, PbusWrapperConfig
    
        class YourPage(PbusPage):
            pass
    
        class YourLocator(PbusLocator):
            pass
    
        class YourSettings(PbusSettings):
            seconds_to_close: int = 1
    
        async with PlaywrightBrowserUserSimulator(
                wrapper_config=PbusWrapperConfig(page_class=YourPage, locator_class=YourLocator),
                settings=YourSettings(),
        ) as browser_context:
            page: YourPage = await browser_context.new_page()
            await page.goto("http://www.playwright.com/")
            await page.wait_to_close()
    ```

## Legal Disclaimer

`pbus` is an open-source browser automation tool intended for legitimate
purposes: automating access to openly distributed content, downloading content
from sites that require an authenticated account and complicate automated
access with overly aggressive bot protection, testing your own web
applications, and personal or academic research.

**The authors do not encourage, endorse or support** unauthorised access to
protected content, circumvention of technical protection measures in violation
of applicable law, violation of website Terms of Service, collection of
personal data without a legal basis, or any activity that infringes copyright
or intellectual property rights.

**You are solely responsible for how you use this tool.** See
[DISCLAIMER.md](DISCLAIMER.md) for the full text.
