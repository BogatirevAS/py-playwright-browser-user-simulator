import typing
from playwright._impl._async_base import AsyncEventContextManager
from playwright.async_api import Response, Download
from typing_extensions import override, Literal

from pbus.classes.page import PbusPage
from pbus.components.decorators.ignore_timeout_error import IgnoreTimeoutError
from pbus.components.decorators.logging_method import LoggingMethod
from pbus.components.decorators.settings_args_injector import PbusSettingsArgsInjector


class CustomPbusPage(PbusPage):
    @override
    @IgnoreTimeoutError()
    @PbusSettingsArgsInjector(
        args_list=["timeout"],
    )
    @LoggingMethod()
    async def goto(
        self,
        url: str,
        *,
        timeout: typing.Optional[float] = None,
        wait_until: typing.Optional[
            Literal["commit", "domcontentloaded", "load", "networkidle"]
        ] = None,
        referer: typing.Optional[str] = None
    ) -> typing.Optional["Response"]:
        return await super().goto(url=url, timeout=timeout, wait_until=wait_until, referer=referer)

    @override
    @PbusSettingsArgsInjector(
        args_list=["timeout"],
    )
    @LoggingMethod()
    def expect_download(
        self,
        predicate: typing.Optional[typing.Callable[["Download"], bool]] = None,
        *,
        timeout: typing.Optional[float] = None
    ) -> AsyncEventContextManager["Download"]:
        return super().expect_download(predicate=predicate, timeout=timeout)

    @override
    @PbusSettingsArgsInjector(
        args_list=["timeout"],
    )
    @LoggingMethod()
    async def wait_for_url(
        self,
        url: typing.Union[str, typing.Pattern[str], typing.Callable[[str], bool]],
        *,
        wait_until: typing.Optional[
            Literal["commit", "domcontentloaded", "load", "networkidle"]
        ] = None,
        timeout: typing.Optional[float] = None
    ) -> None:
        return await super().wait_for_url(url=url, timeout=timeout, wait_until=wait_until)
