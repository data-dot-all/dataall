import logging
import json
from typing import List
from dataall.modules.shares_base.services.sharing_service import ShareData
from dataall.modules.shares_base.services.share_processor_manager import SharesProcessorInterface
from dataall.modules.redshift_datasets_shares.aws.redshift_data import redshift_share_data_client
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftTable
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository

log = logging.getLogger(__name__)


class ProcessRedshiftShare(SharesProcessorInterface):
    def __init__(self, session, share_data, shareable_items, reapply=False):
        self.session = session
        self.share_data: ShareData = share_data
        self.dataset = share_data.dataset
        self.share = share_data.share
        self.tables: List[RedshiftTable] = shareable_items
        self.reapply: bool = reapply
        dataset_connection = RedshiftConnectionRepository.get_redshift_connection(
            self.session, self.dataset.connectionUri
        )
        self.source_admin_connection = dataset_connection
        # TODO: get admin connection for dataset namespace - might not be needed
        # self.source_admin_connection = RedshiftConnectionRepository.get_redshift_admin_connection(
        #     session=self.session,
        #     account_id=self.share_data.source_environment.AwsAccountId,
        #     region=self.share_data.source_environment.region,
        #     namespace=dataset_connection.namespaceId,
        # )
        # The principal of a redshift share request is a string of the form
        # {connectionUri: sxyzaqb, rsRole: redshiftRole1}
        principal = json.loads(share_data.share.principal)
        self.target_admin_connection = RedshiftConnectionRepository.get_redshift_connection(
            session, principal.get('connectionUri')
        )
        self.redshift_role = principal.get('rsRole')

        # There is a unique datashare per dataset per target namespace
        # TODO: prefix of environment or dataall!
        self.datashare_name = (
            f'{self.dataset.name}-{self.dataset.datasetUri}_{self.target_admin_connection.namespaceId}'
        )

    def process_approved_shares(self) -> bool:
        """
        1) (in source namespace) Create datashare for this dataset for this target namespace. If it does not exist yet. One time operation.
        2) (in source namespace) Add schema to the datashare, if not already added. One time operation.
        3) (in source namespace) Add tables to the datashare, if not already added.
        4) (in source namespace) Grant access to the consumer cluster to the datashare, if not already granted. One time operation.
        5) (in target namespace) Create local database from datashare, if it does not exist yet. One time operation.
        6) (in target namespace) Create external schema in local database, if it does not exist yet. One time operation.
        7) (in target namespace) Grant usage access to the redshift role to the schema.
        8) (in target namespace) Grant select access to the requested tables to the redshift role.

        Returns
        -------
        True if share is granted successfully
        """
        log.info('##### Starting Sharing Redshift tables #######')
        success = True
        if not self.tables:
            log.info('No Redshift tables to share. Skipping...')
        else:
            try:
                redshift_client_in_source = redshift_share_data_client(
                    account_id=self.share_data.source_environment.AwsAccountId,
                    region=self.share_data.source_environment.region,
                    connection=self.source_admin_connection,
                )
                existing_datashare = redshift_client_in_source.describe_datashare(self.datashare_name)
                if not existing_datashare:
                    redshift_client_in_source.create_datashare(datashare=self.datashare_name)

                # TODO ADD IF CONDITION FOR SCHEMA NOT IN DATASHARE
                redshift_client_in_source.add_schema_to_datashare(
                    datashare=self.datashare_name, schema=self.dataset.schema
                )
                for table in self.tables:
                    # TODO ADD IF CONDITION FOR table NOT IN DATASHARE
                    redshift_client_in_source.add_table_to_datashare(
                        datashare=self.datashare_name, schema=self.dataset.schema, table_name=table.name
                    )

                # TODO ADD IF CONDITION
                redshift_client_in_source.grant_usage_to_datashare(
                    datashare=self.datashare_name, namespace=self.target_admin_connection.namespaceId
                )

                redshift_client_in_target = redshift_share_data_client(
                    account_id=self.share_data.target_environment.AwsAccountId,
                    region=self.share_data.target_environment.region,
                    connection=self.target_admin_connection,
                )
                # TODO ADD IF CONDITION
                redshift_client_in_target.create_database_from_datashare(
                    database=self.dataset.name,
                    datashare=self.datashare_name,
                    namespace=self.source_admin_connection.namespaceId,
                )
                redshift_client_in_target.create_external_schema(database=self.dataset.name, schema=self.dataset.schema)
                redshift_client_in_target.grant_schema_usage_access_to_redshift_role()
                redshift_client_in_target.grant_select_access_to_tables()
            except Exception as e:
                log.error(f'Failed to process approved tables due to {e}')
                # manager.handle_share_failure_for_all_tables(
                #     tables=self.tables,
                #     error=e,
                #     share_item_status=ShareItemStatus.Share_Approved.value,
                #     reapply=self.reapply,
                # )
                return False
        return success

    def process_revoked_shares(self) -> bool:
        """
        1) Remove tables from the datashare
        2) If no more tables in the datashare
        Returns
        -------
        True if share is granted successfully
        """
        log.info('##### Starting Sharing Redshift tables #######')
        success = True
        if not self.tables:
            log.info('No Redshift tables to share. Skipping...')
        else:
            try:
                redshift_client_in_source = redshift_share_data_client(
                    account_id=self.share_data.source_environment.AwsAccountId,
                    region=self.share_data.source_environment.region,
                    connection=self.source_admin_connection,
                )
            except Exception as e:
                log.error(f'Failed to process revoked tables due to {e}')
                # manager.handle_share_failure_for_all_tables(
                #     tables=self.tables,
                #     error=e,
                #     share_item_status=ShareItemStatus.Share_Approved.value,
                #     reapply=self.reapply,
                # )
                return False
        return success

    def verify_shares(self) -> bool:
        pass
