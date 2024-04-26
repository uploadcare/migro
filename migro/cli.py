#!/usr/bin/env python
"""
    migro.cli
    ~~~~~~~~~

    Command line interface.

"""
import os
import sys
from functools import wraps
from pathlib import Path

import click
from dotenv import dotenv_values, find_dotenv

# Add migro directory to PATH.
parent = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.realpath(parent))

from migro import __version__, settings
from migro.uploader.fetcher import Fetcher

# Find .env file
ENV_FILE_PATH = Path(find_dotenv())
if not ENV_FILE_PATH or ENV_FILE_PATH == Path(''):
    ENV_FILE_PATH = Path('.env')

ENV_FILE_PATH.touch(exist_ok=True)
env = dotenv_values(ENV_FILE_PATH)


def common_options(func):
    """Common options for all uploading commands."""
    @wraps(func)
    @click.option('--upload_base_url', help="Base URL for uploads.", type=str, default=env.get('UPLOAD_BASE'))
    @click.option('--upload_timeout',
                  help="Number of seconds to wait till the file will be processed by `from_url` upload.", type=int,
                  default=env.get('FROM_URL_TIMEOUT'))
    @click.option('--concurrent_uploads', help="Maximum number of upload requests running in 'parallel'.", type=int,
                  default=env.get('MAX_CONCURRENT_UPLOADS'))
    @click.option('--status_check_interval', help="Number of seconds in between status check requests.", type=int,
                  default=env.get('STATUS_CHECK_INTERVAL'))
    def new_func(*args, **kwargs):
        return func(*args, **kwargs)
    return new_func


def update_dotenv(key, value, env_file_path):
    with open(env_file_path, 'r') as file:
        lines = file.readlines()

    key_exists = False
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            key_exists = True
            break

    if not key_exists:
        lines.append(f'{key}={value}\n')

    with open(env_file_path, 'w') as file:
        file.writelines(lines)


def validate_uc_public_key(ctx, param, value):
    if not value:
        raise click.BadParameter('Uploadcare public key cannot be empty. '
                                 'Please specify it through the command line option or environment variable.')
    return value


def validate_s3_bucket(ctx, param, value):
    if not value:
        raise click.BadParameter('AWS S3 bucket name cannot be empty. Please specify it through the command line '
                                 'option or environment variable.')
    return value


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

version_option = click.option("-v", "--version", is_flag=True, callback=show_version,
                              expose_value=False, is_eager=True,
                              help="Show version and quit.")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Migro: A tool for migrating files to Uploadcare."""
    if ctx.invoked_subcommand is None:
        click.echo('Welcome to Migro! Please specify the migration method.\n'
                   'For more information on each method, use the following commands:\n'
                   '  migro s3 --help\n'
                   '  migro urls --help\n'
                   )


@cli.command()
@click.option(
    '--s3_access_key_id',
    help="Your AWS S3 access key ID.",
    type=str
)
@click.option(
    '--s3_secret_access_key',
    help="Your AWS S3 secret access key.",
    type=str
)
@click.option(
    '--s3_bucket_name',
    help="Your S3 bucket name.",
    type=str
)
@click.option(
    '--s3_region',
    help="Your S3 region.",
    type=str
)
@click.option(
    '--uc_public_key',
    help="Your Uploadcare public key.",
    type=str
)
@click.option(
    '--uc_secret_key',
    help="Your Uploadcare secret key.",
    type=str
)
@click.option(
    '--upload_base_url',
    help="Base URL for uploads.",
    type=str
)
@click.option(
    '--upload_timeout',
    help="Number of seconds to wait till the file will be processed by `from_url` upload.",
    type=int
)
@click.option(
    '--concurrent_uploads',
    help="Maximum number of upload requests running in 'parallel'.",
    type=int
)
@click.option(
    '--status_check_interval',
    help="Number of seconds in between status check requests.",
    type=int
)
def init(s3_access_key_id, s3_secret_access_key, s3_bucket_name, s3_region, uc_public_key, uc_secret_key,
         upload_base_url, upload_timeout, concurrent_uploads, status_check_interval):
    """Initialize .env file with credentials and other settings."""

    options = {
        'S3_ACCESS_KEY_ID': s3_access_key_id,
        'S3_SECRET_ACCESS_KEY': s3_secret_access_key,
        'S3_BUCKET_NAME': s3_bucket_name,
        'S3_REGION': s3_region,
        'PUBLIC_KEY': uc_public_key,
        'SECRET_KEY': uc_secret_key,
        'UPLOAD_BASE': upload_base_url,
        'FROM_URL_TIMEOUT': upload_timeout,
        'MAX_CONCURRENT_UPLOADS': concurrent_uploads,
        'STATUS_CHECK_INTERVAL': status_check_interval
    }

    for key, value in options.items():
        if value is not None:
            update_dotenv(key, value, ENV_FILE_PATH)

    click.secho(f"Configuration saved successfully to {ENV_FILE_PATH}", fg='green')


@cli.command()
@click.argument('file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.argument('pub_key', type=str, required=False, default=env.get('PUBLIC_KEY'), callback=validate_uc_public_key)
@click.argument('secret_key', type=str, required=False, default=env.get('SECRET_KEY'))
@common_options
def urls(file, pub_key, secret_key, upload_base_url, upload_timeout, concurrent_uploads, status_check_interval):
    """Migrate files from a file with URLs to Uploadcare."""
    settings.PUBLIC_KEY = pub_key
    settings.SECRET_KEY = secret_key
    settings.UPLOAD_BASE = upload_base_url or settings.UPLOAD_BASE
    settings.FROM_URL_TIMEOUT = upload_timeout or settings.FROM_URL_TIMEOUT
    settings.MAX_CONCURRENT_UPLOADS = concurrent_uploads or settings.MAX_CONCURRENT_UPLOADS
    settings.STATUS_CHECK_INTERVAL = status_check_interval or settings.STATUS_CHECK_INTERVAL

    fetcher = Fetcher()
    fetcher.upload_urls(file)


@cli.command()
@click.argument('bucket_name', type=str, required=False, default=env.get('S3_BUCKET_NAME'), callback=validate_s3_bucket)
@click.argument('pub_key', type=str, required=False, default=env.get('PUBLIC_KEY'), callback=validate_uc_public_key)
@click.argument('secret_key', type=str, required=False, default=env.get('SECRET_KEY'))
@click.option('--s3_access_key_id', type=str, default=env.get('S3_ACCESS_KEY_ID'),
              help="Your AWS S3 access key ID.")
@click.option('--s3_secret_access_key', type=str, default=env.get('S3_SECRET_ACCESS_KEY'),
              help="Your AWS S3 secret access key.")
@click.option('--s3_region', type=str, default=env.get('S3_REGION'),
              help="Your S3 region.")
@common_options
def s3(bucket_name, pub_key, secret_key, s3_access_key_id, s3_secret_access_key, s3_region,
       upload_base_url, upload_timeout, concurrent_uploads, status_check_interval):
    """Migrate files from an S3 bucket to Uploadcare."""
    settings.PUBLIC_KEY = pub_key
    settings.SECRET_KEY = secret_key
    settings.S3_BUCKET_NAME = bucket_name
    settings.S3_ACCESS_KEY_ID = s3_access_key_id
    settings.S3_SECRET_ACCESS_KEY = s3_secret_access_key
    settings.S3_REGION = s3_region
    settings.UPLOAD_BASE = upload_base_url or settings.UPLOAD_BASE
    settings.FROM_URL_TIMEOUT = upload_timeout or settings.FROM_URL_TIMEOUT
    settings.MAX_CONCURRENT_UPLOADS = concurrent_uploads or settings.MAX_CONCURRENT_UPLOADS
    settings.STATUS_CHECK_INTERVAL = status_check_interval or settings.STATUS_CHECK_INTERVAL

    fetcher = Fetcher()
    fetcher.upload_s3()


@cli.command()
def drop():
    """Drop the database, configuration and logs."""
    if not click.confirm('Are you sure you want to drop database, config and logs?'):
        return
    fetcher = Fetcher()
    fetcher.remove_db()
    env_file = Path('.env')
    if env_file.exists():
        env_file.unlink()
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    if logs_dir.exists():
        for log in logs_dir.iterdir():
            log.unlink()

    click.secho('All data dropped successfully.', fg='green')


if __name__ == '__main__':
    cli()
