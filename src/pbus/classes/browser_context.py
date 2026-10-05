import pathlib
import typing
from typing_extensions import override
from playwright._impl._api_structures import StorageState
from playwright.async_api import BrowserContext

from pbus.classes.base_wrapper import PbusBaseWrapper
from pbus.components.decorators.logging_method import LoggingMethod
from pbus.components.decorators.settings_args_injector import PbusSettingsArgsInjector


class PbusBrowserContext(PbusBaseWrapper, BrowserContext):
    def __init__(self, master, browser_context: BrowserContext):
        super().__init__(master, browser_context)

    @override
    @PbusSettingsArgsInjector(
        args_list=["path"],
    )
    @LoggingMethod()
    async def storage_state(
            self,
            *,
            path: typing.Optional[typing.Union[pathlib.Path, str]] = None,
            # indexed_db: typing.Optional[bool] = None,
            **kwargs,
    ) -> StorageState:
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
        return await self.impl_obj.storage_state(
            path=path,
            # indexed_db=indexed_db
            **kwargs,
        )
