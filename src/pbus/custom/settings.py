from pbus.settings.base import PbusSettings


class CustomPbusSettings(PbusSettings):
    save_as_move: bool = True
    default_timeout: float = 60000
    goto_timeout: float = 5000
    wait_for_timeout: float = 120000
    expect_download_timeout: float = 30000
    wait_for_url_timeout: float = 60000
