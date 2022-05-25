import asyncio

import pytest

from migro.uploader import utils
from migro.uploader.utils import session


class MockResponse:
    def __init__(self, json, status):
        self._json = json
        self.status = status

    async def json(self):
        return self._json

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


class Session:
    def __init__(self, response):
        self._response = response

    async def request(self, *args, **kwargs):
        return self._response


@pytest.fixture
def mock_session():
    original_session = utils.session

    fake_response = MockResponse(
        json={
            'token': 'token',
            'status': 'success',
            'uuid': 'file-uuid',
        },
        status=200,
    )
    utils.session = Session(fake_response)

    yield

    utils.session = original_session


@pytest.fixture(scope='session', autouse=True)
def close_session():
    asyncio.ensure_future(session.close())
