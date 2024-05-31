import logging
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset

log = logging.getLogger(__name__)
PIVOT_ROLE_NAME_PREFIX = 'dataallPivotRole'


class LakeFormationDatasetClient:
    def __init__(self, env: Environment, dataset: S3Dataset):
        session = SessionHelper.remote_session(env.AwsAccountId, env.region)
        self._client = session.client('lakeformation', region_name=env.region)
        self._dataset = dataset
        self._env = env

    def check_existing_lf_registered_location(self):
        """
        Checks if there is a non-dataall-created registered location for the Dataset
        Returns False is already existing location else return the resource info
        """

        resource_arn = f'arn:aws:s3:::{self._dataset.S3BucketName}'
        try:
            response = self._client.describe_resource(ResourceArn=resource_arn)
            registered_role_name = response['ResourceInfo']['RoleArn'].lstrip(
                f'arn:aws:iam::{self._dataset.AwsAccountId}:role/'
            )
            log.info(f'LF data location already registered: {response}, registered with role {registered_role_name}')
            if (
                registered_role_name.startswith(PIVOT_ROLE_NAME_PREFIX)
                or response['ResourceInfo']['RoleArn'] == self._dataset.IAMDatasetAdminRoleArn
            ):
                log.info(
                    'The existing data location was created as part of the dataset stack. '
                    'There was no pre-existing data location.'
                )
                return False
            return response['ResourceInfo']

        except ClientError as e:
            log.info(f'LF data location for resource {resource_arn} not found due to {e}')
            return False
