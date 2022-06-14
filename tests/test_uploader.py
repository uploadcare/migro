import asyncio
from unittest.mock import AsyncMock

from migro.uploader.utils import loop, request, session
from migro.uploader.worker import Uploader, Events
from migro import settings, __version__


def test_uploader(mock_session):
    successful = []
    failed = []

    uploader = Uploader(loop=loop)

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


def test_headers():
    settings.PUBLIC_KEY = "public"

    mock = AsyncMock(return_value="ok")

    original_request = session.request
    session.request = mock
    resp = asyncio.run(request('path'))
    session.request = original_request

    expected_ua = f"Migro/{__version__}/public"
    assert expected_ua == mock.call_args.kwargs["headers"]["User-Agent"]

    assert "ok" == resp
