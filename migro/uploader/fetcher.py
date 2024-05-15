"""

    migro.uploader.fetcher
    ~~~~~~~~~~~~~~~~~~~~~~

    File fetcher.

"""
import asyncio

import click
from tqdm import tqdm

from db.db_manager import DBManager, get_db_file
from migro.filestack.utils import build_url
from migro.uploader.s3_client import (AccessDeniedError, S3Client,
                                      UnexpectedError)
from migro.uploader.utils import loop, session
from migro.uploader.worker import Events, Uploader
from migro.utils import save_result_to_csv


def db(func):
    """Decorator for properly connecting and disconnecting to the database."""
    def wrapper(self, *args, **kwargs):
        self.connect_db()
        result = func(self, *args, **kwargs)
        self.disconnect_db()
        return result

    return wrapper


class Fetcher:
    """File fetcher."""
    SOURCES = {
        'URLS': 'urls',
        'S3': 's3'
    }

    def __init__(self):
        self.db_manager = None
        self.attempt = None
        self.bar = None
        self.source = None
        self.s3_client = None
        self.s3_signed_urls = None
        self.uploader = Uploader(loop=loop)
        self.uploader.on(
            Events.DOWNLOAD_COMPLETE,
            Events.UPLOAD_ERROR,
            Events.DOWNLOAD_ERROR,
            callback=self.update_bar)
        self.uploader.on(
            Events.UPLOAD_ERROR,
            Events.DOWNLOAD_ERROR,
            callback=self.append_failed)
        self.uploader.on(Events.DOWNLOAD_COMPLETE, callback=self.append_successful)

    def launch_loop(self, files):
        """Launch the loop for processing files."""
        cancelled = False

        try:
            loop.run_until_complete(self.uploader.process(files))
        except (KeyboardInterrupt, asyncio.CancelledError):
            cancelled = True
        finally:
            self.bar.close()
            asyncio.ensure_future(session.close())
            self.uploader.shutdown()
            result = self.db_manager.finish_attempt(self.attempt)
            file = save_result_to_csv(*result[:2], self.source)
            self.show_final_messages(file, *result[2:])

        loop.close()

        if cancelled:
            click.echo('\n\nFile uploading has been cancelled!')

    def start_upload(self):
        """Start the file uploading."""
        click.echo('Starting upload...')
        files_list = self.db_manager.get_pending_files(self.source)
        if self.source == self.SOURCES['S3']:
            self.s3_signed_urls = {value: key for key, value in self.s3_client.create_signed_urls(files_list).items()}
            files_list = list(self.s3_signed_urls.keys())
        files_count = len(files_list)
        self.attempt: int = self.db_manager.start_attempt(self.source, files_count)
        self.db_manager.set_attempt_for_files(self.attempt)
        self.bar = tqdm(desc='Upload progress',
                        total=files_count,
                        miniters=1,
                        unit='file',
                        dynamic_ncols=True,
                        position=1,
                        maxinterval=3)
        self.launch_loop(files_list)

    def connect_db(self):
        """Connect to the database."""
        self.db_manager = DBManager()

    def disconnect_db(self):
        """Disconnect from the database."""
        self.db_manager.close_connection()

    def update_bar(self, _):
        """Update the progress bar."""
        self.bar.update()

    def insert_file(self, path: str, size=None) -> None:
        """Insert a file into the database."""
        self.db_manager.insert_file(path, self.source, size)

    def append_successful(self, event):
        """Mark the file as successfully uploaded."""
        if self.source == self.SOURCES['S3']:
            file_path = self.s3_signed_urls[event['file'].url]
        else:
            file_path = event['file'].url
        self.db_manager.set_file_uploaded(file_path, self.source, self.attempt, event['file'].uuid)

    def append_failed(self, event):
        """Mark the file as failed to upload."""
        if self.source == self.SOURCES['S3']:
            file_path = self.s3_signed_urls[event['file'].url]
        else:
            file_path = event['file'].url
        self.db_manager.set_file_error(file_path, self.source, event['file'].error)

    @staticmethod
    def show_final_messages(filename, success_count, failed_count):
        """Show the final messages before quitting the program."""
        click.echo('\n\nFile uploading has been finished!')
        click.secho(f'Uploaded files: {success_count}', fg='green' if success_count else 'white')
        click.secho(f'Failed files: {failed_count}', fg='red' if failed_count else 'white')
        click.echo(f'Check the results in "{filename}"')
        click.echo('Thanks for your interest in Uploadcare.')
        click.echo('Hit us up at help@uploadcare.com in case of any questions.')

    @staticmethod
    def remove_db():
        """Removes the database."""
        db_file = get_db_file()
        if get_db_file().exists():
            db_file.unlink()

    @db
    def upload_urls(self, input_file):
        """Upload files from a file with URLs."""
        self.source: str = self.SOURCES['URLS']
        with open(input_file, 'r') as f:
            for line in f:
                self.insert_file(build_url(line.strip()))
        self.start_upload()

    @db
    def upload_s3(self):
        """Upload files from an S3 bucket."""
        self.source: str = self.SOURCES['S3']
        self.s3_client = S3Client()
        click.echo('Checking the credentials...')
        try:
            self.s3_client.check_credentials()
        except (AccessDeniedError, UnexpectedError) as e:
            click.secho(e, fg='red')
            asyncio.ensure_future(session.close())
            return

        click.echo('Credentials are correct.')
        click.echo('Collecting files...')

        for key, size in self.s3_client.get_bucket_contents():
            self.insert_file(key, size)

        self.start_upload()
