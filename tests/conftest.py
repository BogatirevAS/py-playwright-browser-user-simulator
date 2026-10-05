from __future__ import annotations

import asyncio
import functools
import http.server
import socketserver
import threading
from pathlib import Path
from typing import Iterator

import pytest


from pbus import (
    PbusWrapperConfig,
    PbusSettings,
)


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def static_site(tmp_path: Path) -> Iterator[str]:
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text(
        """
        <html><head><title>pbus test</title></head>
        <body>
            <h1 id="title">Hello</h1>
            <a id="dl" href="/file.bin" download>download</a>
            <button id="btn" onclick="document.getElementById('title').textContent='Clicked'">
                click me
            </button>
            <div class="col">1</div>
            <div class="col">2</div>
            <div class="col">3</div>
        </body></html>
        """,
        encoding="utf-8",
    )
    (root / "file.bin").write_bytes(b"\x00\x01\x02" * 100)

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(root)
    )

    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()
            thread.join(timeout=2)


@pytest.fixture()
def base_settings(tmp_path: Path) -> PbusSettings:
    return PbusSettings(
        tmp_path=tmp_path,
        seconds_to_close=0,
    )


@pytest.fixture()
def wrapper_config() -> PbusWrapperConfig:
    return PbusWrapperConfig()
