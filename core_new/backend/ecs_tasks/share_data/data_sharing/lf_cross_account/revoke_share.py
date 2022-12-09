import logging
import uuid

from ..common.lf_share_revoke import LFShareRevoke
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.ram import Ram
from ....aws.handlers.sts import SessionHelper
from ....db import api, models

log = logging.getLogger(__name__)


class CrossAccountShareRevoke(LFShareRevoke):
    def __init__(
        self,
        session,
        shared_db_name: str,
        dataset: models.Dataset,
        share: models.ShareObject,
        shared_tables: [models.DatasetTable],
        source_environment: models.Environment,
        target_environment: models.Environment,
        env_group: models.EnvironmentGroup,
    ):
        super().__init__(
            session,
            shared_db_name,
            dataset,
            share,
            shared_tables,
            source_environment,
            target_environment,
            env_group,
        )

    def revoke_share(self) -> bool:
        """
        Revokes a share cross account
        1) revoke resource link access on target account
        2) revoke table access on source account
        3) delete shared database on target account
        4) revoke external account sharing on source account
        Returns
        -------
        True if revoke is successful
        """

        self.revoke_shared_tables_access()

        self.delete_shared_database()

        if not api.ShareObject.other_approved_share_object_exists(
            self.session,
            self.target_environment.environmentUri,
            self.dataset.datasetUri,
        ):
            self.revoke_external_account_access_on_source_account()

        return True

    def revoke_external_account_access_on_source_account(self) -> [dict]:
        """
        1) Revokes access to external account
        if dataset is not shared with any other team from the same workspace
        2) Deletes resource_shares on RAM associated to revoked tables

        Returns
        -------
        List of revoke entries
        """
        log.info(
            f'Revoking Access for AWS account: {self.target_environment.AwsAccountId}'
        )
        aws_session = SessionHelper.remote_session(
            accountid=self.source_environment.AwsAccountId
        )
        client = aws_session.client(
            'lakeformation', region_name=self.source_environment.region
        )
        revoke_entries = []
        for table in self.shared_tables:

            revoke_entries.append(
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {
                        'DataLakePrincipalIdentifier': self.target_environment.AwsAccountId
                    },
                    'Resource': {
                        'TableWithColumns': {
                            'DatabaseName': table.GlueDatabaseName,
                            'Name': table.GlueTableName,
                            'ColumnWildcard': {},
                            'CatalogId': self.source_environment.AwsAccountId,
                        }
                    },
                    'Permissions': ['DESCRIBE', 'SELECT'],
                    'PermissionsWithGrantOption': ['DESCRIBE', 'SELECT'],
                }
            )
            LakeFormation.batch_revoke_permissions(
                client, self.source_environment.AwsAccountId, revoke_entries
            )
        return revoke_entries

    def delete_ram_resource_shares(self, resource_arn: str) -> [dict]:
        """
        Deletes resource share for the resource arn
        Parameters
        ----------
        resource_arn : glue table arn

        Returns
        -------
        list of ram associations
        """
        log.info(f'Cleaning RAM resource shares for resource: {resource_arn} ...')
        return Ram.delete_resource_shares(
            SessionHelper.remote_session(
                accountid=self.source_environment.AwsAccountId
            ).client('ram', region_name=self.source_environment.region),
            resource_arn,
        )
