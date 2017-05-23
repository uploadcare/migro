"""

    migro.uploader.utils
    ~~~~~~~~~~~~~~~~~~~~

    Helpers functions.

"""
from asyncio import Semaphore, Queue, get_event_loop
from aiohttp import ClientSession, TCPConnector

from urllib.parse import urljoin

from migro import settings

loop = get_event_loop()
upload_semaphore = Semaphore(settings.MAX_CONCURRENT_UPLOADS)
status_check_semaphore = Semaphore(settings.MAX_CONCURRENT_CHECKS)
session = ClientSession(connector=TCPConnector(verify_ssl=False, loop=loop))

event_queue = Queue()
upload_queue = Queue()
status_check_queue = Queue()


async def request(path, params=None):
    """Makes GET upload API request with specific path and params.

    :param path: Request path.
    :param params: Request params.

    :return: aiohttp.ClientResponse.

    """
    path = path.lstrip('/')
    url = urljoin(settings.UPLOAD_BASE, path)

    params['pub_key'] = settings.PUBLIC_KEY
    params['UPLOADCARE_PUB_KEY'] = settings.PUBLIC_KEY

    response = await session.request(
        method='get', url=url, allow_redirects=True, params=params)
    return response
