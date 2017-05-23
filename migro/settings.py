"""

    migro.settings
    ~~~~~~~~~~~~~~

    Utility settings.

"""
# Upload base url.
UPLOAD_BASE = 'https://upload.uploadcare.com/'

# Project public key.
PUBLIC_KEY = '9a598e2a47fe961ea412'

FROM_URL_TIMEOUT = 10

# Maximum number of concurrent upload requests
# Since we use `from_url` feature this will be just GET requests.
MAX_CONCURRENT_UPLOADS = 1

# Maximum number of concurrent jobs to wait of status update of uploaded file.
MAX_CONCURRENT_CHECKS = 20

# Time to wait before next status check, seconds.
STATUS_CHECK_INTERVAL = 3
