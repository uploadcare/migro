"""
    migro.filestack.utils
    ~~~~~~~~~~~~~~~~~~~~~

    Utils and helpers for filestack migration.

"""


def build_url(handle_or_url):
    """Builds URL for filestack-hosted file based on file handler or, 
    if it is already URL - return it."""
    if handle_or_url.startswith('https://') or handle_or_url.startswith('http://'):
        return handle_or_url
    else:
        return 'https://cdn.filestackcontent.com/{0}'.format(handle_or_url)
