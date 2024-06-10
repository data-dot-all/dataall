import logging
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable

log = logging.getLogger(__name__)


class LakeFormationTableClient:
    """Requests to AWS LakeFormation"""

    def __init__(self, table: DatasetTable, aws_session=None):
        if not aws_session:
            aws_session = SessionHelper.remote_session(table.AWSAccountId, table.region)
        self._client = aws_session.client('lakeformation', region_name=table.region)
        self._table = table

    def grant_pivot_role_all_table_permissions(self):
        """
        Pivot role needs to have all permissions
        for tables managed inside dataall
        """
        table = self._table
        principal = SessionHelper.get_delegation_role_arn(table.AWSAccountId, table.region)
        self._grant_permissions_to_table(principal, ['SELECT', 'ALTER', 'DROP', 'INSERT'])

    def grant_principals_all_table_permissions(self, principals: [str]):
        """
        Update the table permissions on Lake Formation
        for tables managed by data.all
        :param principals:
        :return:
        """

        for principal in principals:
            try:
                self._grant_permissions_to_table(principal, ['ALL'])
            except ClientError:
                pass  # ignore the error to continue with other requests

    def _grant_permissions_to_table(self, principal, permissions):
        table = self._table
        try:
            grant_dict = dict(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'Table': {
                        'DatabaseName': table.GlueDatabaseName,
                        'Name': table.name,
                    }
                },
                Permissions=permissions,
            )
            response = self._client.grant_permissions(**grant_dict)
            log.error(
                f'Successfully granted pivot role all table '
                f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                f'access: {response}'
            )
        except ClientError as e:
            log.error(
                f'Failed to grant pivot role all table '
                f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                f'access: {e}'
            )
            raise e
