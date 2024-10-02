import logging
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class S3Client:
    def __init__(self, session, region):
        self._client = session.client('s3', region_name=region)
        self._resource = session.resource('s3', region_name=region)
        self._region = region

    def delete_bucket(self, bucket_name):
        """
        Delete an S3 bucket.
        :param bucket_name: Name of the S3 bucket to be deleted
        :return: None
        """
        try:
            # Delete all objects in the bucket before deleting the bucket
            bucket = self._resource.Bucket(bucket_name)
            bucket_versioning = self._resource.BucketVersioning(bucket_name)
            if bucket_versioning.status == 'Enabled':
                bucket.object_versions.delete()
            else:
                bucket.objects.all().delete()
            self._client.delete_bucket(Bucket=bucket_name)
        except ClientError as e:
            log.exception(f'Error deleting S3 bucket: {e}')
