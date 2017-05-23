#!/usr/bin/env python3.5
"""
    migro.cli
    ~~~~~~~~~

    Command line interface.

"""
import sys
import os

# Add migro directory to PATH.
parent = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.realpath(parent))

import click
from migro import settings
from migro import __version__


# def ask_exit():
#     """Loop and tasks shutdown callback."""
#     print("EXIT")
#     loop.stop()
#     pending = asyncio.Task.all_tasks()
#     for task in pending:
#         task.cancel()
#
#     # Run loop until tasks done.
#     f = asyncio.gather(*pending)
#     f.cancel()
#     loop.run_until_complete(f)
#
# # Register SIGINT and SIGTERM signals for shutdown.
# for signame in ('SIGINT', 'SIGTERM'):
#     loop.add_signal_handler(getattr(signal, signame), ask_exit)
#
# urls = [
#             'https://ucarecdn.com/9e383a6b-35a5-4612-ad86-5f84c64a152b/',
#             'https://ucarecdn.com/1e8223ff-5c64-4660-8841-e39a83bd408c/',
#             'https://ucarecdn.com/6a200842-df2e-4dd6-9bcd-060237c99d44/',
#             'https://ucarecdn.com/0fc29660-becc-416d-a4da-85c68ed452d3/',
#             'https://ucarecdn.com/03452277-724a-40ff-8ff8-3d50801fcbe8/'
#         ]
# uploader = Uploader(loop=loop)
#
# try:
#     loop.run_until_complete(uploader.process(urls))
# except KeyboardInterrupt:
#     pass
# finally:
#     session.close()
#     uploader.shutdown()
#
# loop.close()
#


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

public_key_option = click.argument(
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
    help='Uploadcare upload base URL.',
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
    help='Maximum number of \'parallel\' upload requests.',
    type=int)

max_concurrent_checks_option = click.option(
    '-mc', '--max_checks',
    default=settings.MAX_CONCURRENT_CHECKS,
    show_default=True,
    help='Maximum number of \'parallel\' `from_url` status check requests.',
    type=int)

status_check_interval_option = click.option(
    '-ci', '--check_interval',
    default=settings.STATUS_CHECK_INTERVAL,
    help='Number of seconds to wait between each requests of status check for '
         'one uploaded file.',
    type=float)

input_file_option = click.argument(
    'input_file',
    required=True,
    # help='Input file with files IDs/URLs to migrate.',
    type=click.File('rb')
)

output_file_option = click.option(
    '-o', '--output',
    help='Path to output file for results.',
    show_default=True,
    default='migro_result.txt',
    type=click.File('wb'),
)


@click.command(help='Migrate your files to Uploadcare.')
@show_version_option
@help_option
@public_key_option
@input_file_option
@output_file_option
@upload_base_option
@from_url_timeout_option
@max_concurrent_checks_option
@status_check_interval_option
def cli(**options):
    """Migrate your files to Uploadcare."""
    print(options, 'HELLO')



if __name__ == '__main__':
    cli()
