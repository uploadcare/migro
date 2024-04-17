import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from botocore.paginate import PageIterator
from typing import Tuple, Generator, List, Dict
from migro import settings


class AccessDeniedError(Exception):
    pass


class UnexpectedError(Exception):
    pass


class ObjectNotFoundError(Exception):
    pass


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
        """Check if the credentials are valid."""
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            pages: PageIterator = paginator.paginate(Bucket=self.bucket_name)
        except NoCredentialsError:
            raise
        except ClientError as e:
            if e.response['Error']['Code'] == '403':
                raise AccessDeniedError('Access Denied. The credentials do not allow ListObjects operation.')
            else:
                raise UnexpectedError(f'An unexpected error occurred: {e}')

        for page in pages:
            if 'Contents' in page and page['Contents']:
                first_object_key = page['Contents'][0]['Key']
                try:
                    self.s3.get_object(Bucket=self.bucket_name, Key=first_object_key)
                    break
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == '403':
                        raise AccessDeniedError('Access Denied. The credentials do not allow GetObject operation.')
                    elif error_code == '404':
                        raise ObjectNotFoundError(
                            'You don\' have any objects in bucket.')
                    else:
                        raise UnexpectedError(f'An unexpected error occurred: {e}')

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
