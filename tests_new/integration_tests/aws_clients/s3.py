import logging
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class S3Client:
    def __init__(self, session, account, region):
        self._client = session.client('s3', region_name=region)
        self._control_client = session.client('s3control', region_name=region)
        self._resource = session.resource('s3', region_name=region)
        self._account = account
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
            # Delete all object versions
            bucket.object_versions.all().delete()
            # Delete any remaining objects (if versioning was not enabled)
            bucket.objects.all().delete()
            # Delete any remaining access point
            access_points = self._control_client.list_access_points(AccountId=self._account, Bucket=bucket_name)[
                'AccessPointList'
            ]
            for access_point in access_points:
                self._control_client.delete_access_point(AccountId=self._account, Name=access_point['Name'])
            bucket.delete()
        except ClientError as e:
            log.exception(f'Error deleting S3 bucket: {e}')
