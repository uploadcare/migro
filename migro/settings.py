"""

    migro.settings
    ~~~~~~~~~~~~~~

    Utility settings.

"""
# Upload base url.
UPLOAD_BASE = 'https://upload.uploadcare.com/'

# Project public key.
PUBLIC_KEY = None

# Timeout for status check of file uploaded by `from_url`.
# If you have big files - you can increase this option.
FROM_URL_TIMEOUT = 30

# Maximum number of concurrent upload requests
# Since we use `from_url` feature this will be just GET requests.
MAX_CONCURRENT_UPLOADS = 20

# Maximum number of concurrent jobs to wait of status update of uploaded file.
MAX_CONCURRENT_CHECKS = 20

# Time to wait before next status check, seconds.
STATUS_CHECK_INTERVAL = 0.3
