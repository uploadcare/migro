"""

    migro.settings
    ~~~~~~~~~~~~~~

    Utility settings.

"""
# Upload base url.
UPLOAD_BASE = 'https://upload.uploadcare.com/'

# Project public key.
PUBLIC_KEY = None

# Project secret key
SECRET_KEY = None

# Timeout for status check of file uploaded by `from_url`.
# If you have big files - you can increase this option.
FROM_URL_TIMEOUT = 30

# Maximum number of concurrent upload requests
MAX_CONCURRENT_UPLOADS = 20

# Time to wait before next status check, seconds.
STATUS_CHECK_INTERVAL = 0.3

# Throttling timeout sleep interval
THROTTLING_TIMEOUT = 5.0

# S3 access key ID.
S3_ACCESS_KEY_ID = None

# S3 secret access key.
S3_SECRET_ACCESS_KEY = None

# S3 bucket name.
S3_BUCKET_NAME = None

# S3 region.
S3_REGION = None

# S3 signed URL expiration time, seconds.
S3_URL_EXPIRATION_TIME = 86400
