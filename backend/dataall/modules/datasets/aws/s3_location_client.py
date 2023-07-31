import logging

from dataall.base.aws.sts import SessionHelper
from dataall.modules.datasets_base.db.models import DatasetStorageLocation

log = logging.getLogger(__name__)


class S3LocationClient:

    def __init__(self, location: DatasetStorageLocation):
        session = SessionHelper.remote_session(accountid=location.AWSAccountId)
        self._client = session.client('s3', region_name=location.region)
        self._location = location

    def create_bucket_prefix(self):
        location = self._location
        try:
            response = self._client.put_object(
                Bucket=location.S3BucketName, Body='', Key=location.S3Prefix + '/'
            )
            log.info(
                'Creating S3 Prefix `{}`({}) on AWS #{}'.format(
                    location.S3BucketName, location.AWSAccountId, response
                )
            )
        except Exception as e:
            log.error(
                f'Dataset storage location creation failed on S3 for dataset location {location.locationUri} : {e}'
            )
            raise e
