from migro.uploader.utils import loop
from migro.uploader.worker import Uploader, Events


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
