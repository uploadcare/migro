"""

    migro.uploader.utils
    ~~~~~~~~~~~~~~~~~~~~

    Helpers functions.

"""
from asyncio import get_event_loop
from urllib.parse import urljoin
from datetime import datetime, timedelta
import time
import hashlib
import hmac

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

    if (settings.SECRET_KEY):
        expire_timestamp = generate_expire_timestamp()
        upload_signature = generate_secure_signature(settings.SECRET_KEY, expire_timestamp)

        params['signature'] =  upload_signature
        params['expire'] = expire_timestamp

    response = await session.request(
        method='get', url=url, allow_redirects=True, params=params)
    return response


def generate_expire_timestamp(minutes_ahead=5):
    """Generate expiration timestamp for specified minutes after current time.

    :param minutes_ahead: Minutes after current time.

    :return: int.

    """
    expire_timestamp = int(time.time()) + 60 * minutes_ahead

    return expire_timestamp


def generate_secure_signature(secret, expire):
    """Generate secure signature with specified secret and expiration timestamp.

    :param secret: Secret Key.
    :param expire: Expiration timestamp.

    :return: str.

    """
    k, m = secret, str(expire).encode('utf-8')
    if not isinstance(k, (bytes, bytearray)):
        k = k.encode('utf-8')

    return hmac.new(k, m, hashlib.sha256).hexdigest()
