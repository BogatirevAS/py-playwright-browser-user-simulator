from typing import TypeVar, Generic, override
from playwright._impl._async_base import AsyncEventInfo

from pbus.classes.base_wrapper import PbusBaseWrapper

T = TypeVar('T')


class PbusAsyncEventInfo(PbusBaseWrapper, AsyncEventInfo, Generic[T]):
    def __init__(self, master, event_info: AsyncEventInfo[T]):
        self._impl_obj = event_info
        super().__init__(master, event_info._future)

    @override
    @property
    async def value(self) -> T:
        # TODO: It's a temporary solution; ideally, the property should be wrapped in `base_wrapper`.
        return self.wrapper_config.create_wrapper(self, await self._impl_obj.value, False)
