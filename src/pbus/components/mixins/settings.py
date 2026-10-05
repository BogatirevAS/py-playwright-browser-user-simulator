from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pbus.settings.base import PbusSettings


class PbusSettingsMixin:
    def __init__(self, settings: "PbusSettings", *args, **kwargs):
        self._settings = settings
        super().__init__(*args, **kwargs)

    @property
    def settings(self):
        return self._settings
