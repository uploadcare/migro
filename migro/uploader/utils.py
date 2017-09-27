"""

    migro.uploader.utils
    ~~~~~~~~~~~~~~~~~~~~

    Helpers functions.

"""
from asyncio import get_event_loop
from urllib.parse import urljoin

from aiohttp import ClientSession, TCPConnector

from migro import settings

loop = get_event_loop()
session = ClientSession(connector=TCPConnector(verify_ssl=False, loop=loop))


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
