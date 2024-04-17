import boto3
from botocore.exceptions import ClientError
from typing import Tuple, Generator, List, Dict
from migro import settings


class S3ClientException(Exception):
    """Base class for S3Client exceptions. """
    pass


class AccessDeniedError(S3ClientException):
    def __init__(self, message):
        super().__init__(f"Access Denied: {message}")


class UnexpectedError(S3ClientException):
    def __init__(self, message):
        super().__init__(f"An unexpected error occurred: {message}")


class S3Client:
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
        )

    def check_credentials(self) -> None:
        """Check if the credentials are valid and have access to list and get objects."""
        paginator = self.s3.get_paginator('list_objects_v2')
        operation = "ListObjects"
        try:
            for page in paginator.paginate(Bucket=self.bucket_name):
                operation = "GetObject"
                if 'Contents' in page:
                    for obj in page['Contents']:
                        self.s3.get_object(Bucket=self.bucket_name, Key=obj['Key'])
                        return
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise AccessDeniedError(f"The AWS credentials provided do not have permission "
                                        f"to perform the '{operation}'.")
            elif error_code in ['NoSuchBucket', 'NoSuchKey']:
                raise AccessDeniedError(
                    "The specified bucket or key does not exist.")
            else:
                raise UnexpectedError(str(e))

    def get_bucket_contents(self) -> Generator[Tuple[str, int], None, None]:
        """Get the contents of the bucket."""
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name)

        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                size = obj['Size']
                yield key, size

    def create_signed_urls(self, keys: List) -> Dict:
        """
        Create signed URLs for a list of file keys.
        """
        signed_urls = {}
        for key in keys:
            signed_url: Dict = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=settings.S3_URL_EXPIRATION_TIME
            )
            signed_urls[key] = signed_url
        return signed_urls
