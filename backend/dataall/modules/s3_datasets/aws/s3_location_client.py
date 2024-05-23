import logging

from dataall.base.aws.sts import SessionHelper
from dataall.modules.s3_datasets.db.dataset_models import DatasetStorageLocation, S3Dataset

log = logging.getLogger(__name__)


class S3LocationClient:
    def __init__(self, location: DatasetStorageLocation, dataset: S3Dataset):
        """
        It first starts a session assuming the pivot role,
        then we define another session assuming the dataset role from the pivot role
        """
        pivot_role_session = SessionHelper.remote_session(accountid=location.AWSAccountId, region=location.region)
        session = SessionHelper.get_session(base_session=pivot_role_session, role_arn=dataset.IAMDatasetAdminRoleArn)
        self._client = session.client('s3', region_name=location.region)
        self._location = location

    def create_bucket_prefix(self):
        location = self._location
        try:
            response = self._client.put_object(Bucket=location.S3BucketName, Body='', Key=location.S3Prefix + '/')
            log.info(
                'Creating S3 Prefix `{}`({}) on AWS #{}'.format(location.S3BucketName, location.AWSAccountId, response)
            )
        except Exception as e:
            log.error(
                f'Dataset storage location creation failed on S3 for dataset location {location.locationUri} : {e}'
            )
            raise e
