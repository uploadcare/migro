import sys
from enum import Enum
from typing import Optional
import asyncio
from tqdm import tqdm
import signal
import click

from migro.uploader.loop import *
from migro.uploader.worker import Uploader, Events, File
from migro.uploader.utils import loop, session
from migro.filestack.utils import build_url
from db.db_manager import DBManager

db_manager: Optional[DBManager] = None


# method: Optional[str] = None


def db(func):
    def wrapper(self, *args, **kwargs):
        self.connect_db()
        result = func(self, *args, **kwargs)
        self.disconnect_db()
        return result

    return wrapper


class Sources(Enum):
    """Available file sources."""
    URLS = 'urls'
    S3 = 's3'

    def __str__(self):
        return self.value


class UploadSources:
    def __init__(self, settings):
        self.db_manager = None
        self.attempt = None
        self.bar = None
        self.source = None
        self.settings = settings
        self.uploader = Uploader(loop=loop)
        self.uploader.on(Events.DOWNLOAD_COMPLETE, Events.UPLOAD_ERROR,
                         Events.DOWNLOAD_ERROR,
                         callback=self.update_bar)
        self.uploader.on(Events.UPLOAD_ERROR, Events.DOWNLOAD_ERROR,
                         callback=self.append_failed)
        self.uploader.on(Events.DOWNLOAD_COMPLETE, callback=self.append_successful)

    def start_upload(self, source, files_count):
        self.attempt: int = db_manager.start_attempt(source, files_count)

    def connect_db(self):
        self.db_manager = DBManager()

    def disconnect_db(self):
        self.db_manager.close_connection()

    def update_bar(self):
        self.bar.update()

    def append_successful(self, event):
        db_manager.set_file_uploaded(event['file'].url, self.source, self.attempt, event['file'].uuid)

    def append_failed(self, event):
        db_manager.set_file_error(event['file'].url, self.source, event['file'].error)

    @db
    def upload_urls(self, settings, input_file, output_file):
        self.source: str = Sources.URLS.value
        with open(input_file, 'r') as f:
            input_file_content = f.readlines()
        files_list = [build_url(url.strip()) for url in input_file_content]
        files_count = len(files_list)
        self.start_upload(self.source, files_count)
        self.bar = tqdm(desc='Upload progress',
                        total=files_count,
                        miniters=1,
                        unit='file',
                        dynamic_ncols=True,
                        position=1,
                        maxinterval=3)
        failed = []
        successful = []
        cancelled = False

        try:
            loop.run_until_complete(self.uploader.process(files_list))
        except (KeyboardInterrupt, asyncio.CancelledError):
            cancelled = True
        finally:
            db_manager.finish_attempt(self.attempt)
            self.bar.close()
            asyncio.ensure_future(session.close())
            self.uploader.shutdown()

        loop.close()

        # with open(output_file, 'w') as output:
        #     for file in successful:
        #         ucare_url = 'https://ucarecdn.com/{0}/'.format(file.uuid)
        #         output.write('{0}\t{1}\t{2}\n'.format(file.url, 'success',
        #                                               ucare_url))
        #     for file in failed:
        #         output.write('{0}\t{1}\t{2}\n'.format(file.url, 'fail',
        #                                               file.error))

        if cancelled:
            click.echo('\n\nFile uploading has been cancelled!!')
            num_files = 'Some({0})'.format(len(successful + failed))
        else:
            num_files = 'All'

        click.echo('\n\n{0} files have been processed, output URLs were written '
                   'to: are here: {1}'.format(num_files, output_file))
        if failed:
            click.echo('Number of failed files: {0}'.format(len(failed)))
        click.echo('Thanks for your interest in Uploadcare.')
        click.echo('Hit us up at help@uploadcare.com in case of any questions.\n')        
