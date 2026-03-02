import asyncio
from unittest.mock import AsyncMock, patch

from migro import __version__, settings
from migro.uploader.utils import request
from migro.uploader.worker import Events, Uploader


def test_uploader(mock_session):
    successful = []
    failed = []
    loop = asyncio.new_event_loop()
    uploader = Uploader(loop=loop)

    try:
        uploader.on(
            Events.UPLOAD_ERROR,
            Events.DOWNLOAD_ERROR,
            callback=lambda event: failed.append(event['file']),
        )

        uploader.on(
            Events.DOWNLOAD_COMPLETE,
            callback=lambda event: successful.append(event['file']),
        )

        urls = ['http://file-url']
        loop.run_until_complete(uploader.process(urls))

        uploader.shutdown()

        assert successful
        assert not failed
    finally:
        if not loop.is_closed():
            loop.close()


@patch("migro.uploader.utils.get_session")
def test_headers(mock_get_session):
    settings.PUBLIC_KEY = "public"

    request_mock = AsyncMock(return_value="ok")
    session_stub = type("SessionStub", (), {"request": request_mock})()
    mock_get_session.return_value = session_stub
    resp = asyncio.run(request("path"))

    expected_ua = f"Migro/{__version__}/public"
    assert expected_ua == request_mock.call_args.kwargs["headers"]["User-Agent"]

    assert "ok" == resp
