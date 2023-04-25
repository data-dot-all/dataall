import logging
from botocore.exceptions import ClientError

from dataall.aws.handlers.sts import SessionHelper
from dataall.db.models import DatasetTable

log = logging.getLogger(__name__)


class LakeFormationTableClient:
    """Requests to AWS LakeFormation"""

    def __init__(self, aws_session, table: DatasetTable):
        self._client = aws_session.client('lakeformation', region_name=table.reg)
        self._table = table

    def grant_pivot_role_all_table_permissions(self):
        """
        Pivot role needs to have all permissions
        for tables managed inside dataall
        :param aws_session:
        :param table:
        :return:
        """
        table = self._table
        try:
            grant_dict = dict(
                Principal={
                    'DataLakePrincipalIdentifier': SessionHelper.get_delegation_role_arn(
                        table.AWSAccountId
                    )
                },
                Resource={
                    'Table': {
                        'DatabaseName': table.GlueDatabaseName,
                        'Name': table.name,
                    }
                },
                Permissions=['SELECT', 'ALTER', 'DROP', 'INSERT'],
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
