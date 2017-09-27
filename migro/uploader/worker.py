"""

    migro.uploader.worker
    ~~~~~~~~~~~~~~~~~~~~~

    File uploader worker.

"""
import asyncio
import time
from collections import defaultdict
from enum import Enum
from uuid import uuid4

from migro import settings
from migro.uploader.utils import request


class Events(Enum):
    """Available events."""
    UPLOAD_ERROR = 'UPLOAD_ERROR'
    UPLOAD_COMPLETE = 'UPLOAD_COMPLETE'
    # Download on Uploadcare side.
    DOWNLOAD_ERROR = 'DOWNLOAD_ERROR'
    DOWNLOAD_COMPLETE = 'DOWNLOAD_COMPLETE'

    def __str__(self):
        return self.value


class File:
    """An uploading file instance.
    
    :param error: Current file migration error.
    :param uuid: Uploaded to uploadcare file id .
    :param upload_token: `from_url` upload token.
    :param data: Uploaded to uploadcare file data.
    :param url: `from_url` file url - from where to download it.
    :param id: local file id.

    """
    def __init__(self, url):
        self.error = None
        self.uuid = None
        self.upload_token = None
        self.data = None
        self.url = url
        self.id = uuid4()

    @property
    def status(self):
        if self.error:
            return 'error'
        elif self.upload_token and not self.uuid:
            return 'uploaded'
        elif self.upload_token and self.uuid:
            return 'complete'


class Uploader:
    """An uploader worker.
    
    :param loop: Uploader event loop.
    :param EVENTS: Set of available events to listen.
    :param events_callbacks: Registry of events callbacks.
    :param upload_semaphore: Semaphore for upload tasks.
    :param status_check_semaphore: Semaphore for status check tasks.
    :param event_queue: Events queue.
    :param upload_queue: Upload queue.

    """
    EVENTS = (Events.UPLOAD_ERROR,
              Events.UPLOAD_COMPLETE,
              Events.DOWNLOAD_ERROR,
              Events.DOWNLOAD_COMPLETE)

    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._events_callbacks = defaultdict(list)
        self.loop = loop
        # Semaphores to avoid too much 'parallel' requests.
        self._upload_semaphore = asyncio.Semaphore(
            settings.MAX_CONCURRENT_UPLOADS, loop=self.loop)
        self.event_queue = asyncio.Queue(loop=self.loop)
        self.upload_queue = asyncio.Queue(loop=self.loop)

    async def upload(self, file):
        """Upload file using `from_url` feature.
        
        :param file: `File` instance.
        
        """
        async with self._upload_semaphore:
            data = {'source_url': file.url, 'store': 'auto'}
            response = await request('from_url/', data)

            if response.status != 200:
                file.error = 'UPLOAD_ERROR: {0}'.format(await response.text())
                event = {'type': Events.UPLOAD_ERROR, 'file': file}
            else:
                file.upload_token = (await response.json())['token']
                event = {'type': Events.UPLOAD_COMPLETE, 'file': file}

            # Create event.
            asyncio.ensure_future(self.event_queue.put(event), loop=self.loop)
            await self.wait_for_status(file)
            # Mark file as processed from upload queue.
            self.upload_queue.task_done()

            return None

    async def wait_for_status(self, file):
        """Wait till `file` will be processed by Uploadcare or 
        `settings.FROM_URL_TIMEOUT` seconds before timeout.
        
        :param file: `File` instance.
    
        """
        start = time.time()
        event = {'file': file}
        data = {'token': file.upload_token}
        while time.time() - start <= settings.FROM_URL_TIMEOUT:
            response = await request('from_url/status/', data)
            if response.status != 200:
                event['type'] = Events.DOWNLOAD_ERROR
                file.error = 'Request error: {0}'.format(response.status)
                break
            else:
                result = await response.json()
                if 'error' in result:
                    event['type'] = Events.DOWNLOAD_ERROR
                    file.error = result['error']
                    break
                elif result['status'] == 'success':
                    event['type'] = Events.DOWNLOAD_COMPLETE
                    file.data = result
                    file.uuid = result['uuid']
                    break
                else:
                    await asyncio.sleep(settings.STATUS_CHECK_INTERVAL)
        else:
            # `from_url` timeout.
            event['type'] = Events.DOWNLOAD_ERROR
            file.error = 'Status check timeout.'

        # Mark file as processed from status check queue.
        asyncio.ensure_future(self.event_queue.put(event), loop=self.loop)
        return None

    async def process_upload_queue(self):
        """Upload queue process coroutine."""
        while True:
            file = await self.upload_queue.get()
            asyncio.ensure_future(self.upload(file), loop=self.loop)
        return None

    async def process(self, urls):
        """Process `urls` - upload specified urls to Uploadcare.
        
        :param urls: List of URL's to upload to Uploadcare.
        
        """
        self._consumers = [
            asyncio.ensure_future(self.process_events(), loop=self.loop),
            asyncio.ensure_future(self.process_upload_queue(), loop=self.loop),
        ]
        for url in urls:
            # Put jobs into upload queue.
            await self.upload_queue.put(File(url))

        # Wait till all queues are processed
        await self.upload_queue.join()
        return None

    def shutdown(self):
        """Shutdown uploader.
        
        Stop all consumers, wait till they stop.
        
        """
        for consumer in self._consumers:
            consumer.cancel()
        try:
            # Wait till started consumers tasks will finish.
            self.loop.run_until_complete(asyncio.gather(*self._consumers,
                                                        loop=self.loop))
        except asyncio.CancelledError:
            pass

        # Remove all the queues consumers.
        self._consumers = []
        return None

    async def process_events(self):
        """Events process coroutine."""
        while True:
            event = await self.event_queue.get()
            event_type = event['type']
            callbacks = self._events_callbacks[event_type]
            for callback in callbacks:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.ensure_future(callback(event), loop=self.loop)
                else:
                    callback(event)
        return None

    def on(self, *events, callback):
        """Register `callback` for `event`.
        
        The callbacks will be executed in registration order.
        In case if callback is coroutine - the callback will be scheduled to 
        execute in `self.loop` loop.
        
        :param event: Event instance.
        :param callback: Callback to register. 
        
        """
        for event in events:
            if event not in self.EVENTS:
                raise TypeError('Unknown event')

            self._events_callbacks[event].append(callback)
        return None

    def off(self, *events, callback=None):
        """Unregister specific callback or all callbacks for event.
        
        :param event: Event instance.
        :param callback: Callback to unregister.
        
        """
        for event in events:
            if event not in self.EVENTS:
                raise TypeError('Unknown event')

            if event in self._events_callbacks:
                if callback:
                    callbacks = self._events_callbacks[event]
                    if callback in callbacks:
                        callbacks.remove(callback)
                else:
                    del self._events_callbacks[event]
        return None
