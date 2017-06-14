#!/usr/bin/env python3.5
"""
    migro.cli
    ~~~~~~~~~

    Command line interface.

"""
import os
import sys

# Add migro directory to PATH.
parent = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.realpath(parent))

import asyncio
import click
from tqdm import tqdm
import signal

from migro import settings, __version__
from migro.uploader.worker import Uploader, Events
from migro.uploader.utils import loop, session
from migro.filestack.utils import build_url


def ask_exit():
    """Loop and tasks shutdown callback."""
    pending = asyncio.Task.all_tasks()
    for task in pending:
        task.cancel()

# Register SIGINT and SIGTERM signals for shutdown.
for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(getattr(signal, signame), ask_exit)


def show_version(ctx, param, value):
    """Show version and quit."""
    if value and not ctx.resilient_parsing:
        version = "Uploadcare migration tool (Migro): {}".format(__version__)
        click.echo(version, color=ctx.color)
        ctx.exit()


def show_help(ctx, param, value):
    """Show help and quit."""
    if value and not ctx.resilient_parsing:
        click.echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

help_option = click.option("-h", "--help", is_flag=True, callback=show_help,
                           expose_value=False, is_eager=True,
                           help="Show this help and quit.")

show_version_option = click.option(
    "-v", "--version",
    is_flag=True,
    callback=show_version,
    expose_value=False,
    is_eager=True,
    help="Show utility version and quit.")

public_key_arg = click.argument(
    'public_key',
    required=True,
    # help='Your Uploadcare project public key.',
    # prompt='PROJECT PUBLIC KEY',
    type=str,
    is_eager=True)

upload_base_option = click.option(
    '-ub', '--upload_base',
    default=settings.UPLOAD_BASE,
    show_default=True,
    help='Base URL for uploads.',
    type=str)

from_url_timeout_option = click.option(
    '-fut', '--from_url_timeout',
    default=settings.FROM_URL_TIMEOUT,
    show_default=True,
    help='Number of seconds to wait till the file will be processed by '
         '`from_url` upload.',
    type=float)

max_concurrent_upload_option = click.option(
    '-mu', '--max_uploads',
    default=settings.MAX_CONCURRENT_UPLOADS,
    show_default=True,
    help='Maximum number of upload requests running in \'parallel\'.',
    type=int)

max_concurrent_checks_option = click.option(
    '-mc', '--max_checks',
    default=settings.MAX_CONCURRENT_CHECKS,
    show_default=True,
    help='Maximum number of `from_url` status check requests running in '
         '\'parallel\'.',
    type=int)

status_check_interval_option = click.option(
    '-ci', '--check_interval',
    default=settings.STATUS_CHECK_INTERVAL,
    help='Number of seconds in between status check requests.',
    type=float)

input_file_arg = click.argument(
    'input_file',
    required=True,
    # help='Input file with files IDs/URLs to migrate.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False,
                    readable=True))

output_file_option = click.option(
    '-o', '--output_file',
    help='Path to a Migro output file.',
    show_default=True,
    default='migro_result.txt',
    type=click.Path(file_okay=True, dir_okay=False, writable=True,
                    resolve_path=True))


@click.command(help='Migrate your files to Uploadcare.')
@show_version_option
@help_option
@public_key_arg
@input_file_arg
@output_file_option
@upload_base_option
@from_url_timeout_option
@max_concurrent_upload_option
@max_concurrent_checks_option
@status_check_interval_option
def cli(public_key, input_file, output_file, upload_base, from_url_timeout,
        max_uploads, max_checks, check_interval):
    """Migrate your files to Uploadcare."""
    # Set settings from the cli args.
    settings.PUBLIC_KEY = public_key
    settings.UPLOAD_BASE = upload_base
    settings.FROM_URL_TIMEOUT = from_url_timeout
    settings.MAX_CONCURRENT_UPLOADS = max_uploads
    settings.MAX_CONCURRENT_CHECKS = max_checks
    settings.STATUS_CHECK_INTERVAL = check_interval

    with open(input_file, 'r') as f:
        urls = f.readlines()
    urls = [build_url(url.strip()) for url in urls]

    bar = tqdm(desc='Upload progress',
               total=len(urls),
               miniters=1,
               unit='file',
               dynamic_ncols=True,
               position=1,
               maxinterval=3)
    failed = []
    successful = []
    cancelled = False

    def update_bar(_): bar.update()
    def append_successful(event): successful.append(event['file'])
    def append_failed(event): failed.append(event['file'])

    uploader = Uploader(loop=loop)
    uploader.on(Events.DOWNLOAD_COMPLETE, Events.UPLOAD_ERROR,
                Events.DOWNLOAD_ERROR,
                callback=update_bar)
    uploader.on(Events.UPLOAD_ERROR, Events.DOWNLOAD_ERROR,
                callback=append_failed)
    uploader.on(Events.DOWNLOAD_COMPLETE, callback=append_successful)

    try:
        loop.run_until_complete(uploader.process(urls))
    except (KeyboardInterrupt, asyncio.CancelledError):
        cancelled = True
    finally:
        bar.close()
        session.close()
        uploader.shutdown()

    loop.stop()
    loop.close()

    with open(output_file, 'w') as output:
        for file in successful:
            ucare_url = 'https://ucarecdn.com/{0}/'.format(file.uuid)
            output.write('{0}\t{1}\t{2}\n'.format(file.url, 'success',
                                                  ucare_url))
        for file in failed:
            output.write('{0}\t{1}\t{2}\n'.format(file.url, 'failed',
                                                  file.error))

    if cancelled:
        click.echo('\n\nFile uploading has been cancelled!!')
        num_files = 'Some({0})'.format(len(successful + failed))
    else:
        num_files = 'All'

    click.echo('\n\n{0} files have been processed, output URLs were written '
               'to: are here: {1}'.format(num_files, output_file))
    click.echo('Thanks for your interest in Uploadcare.')
    click.echo('Hit us up at help@uploadcare.com in case of any questions.')
    click.echo('')

if __name__ == '__main__':
    cli()
