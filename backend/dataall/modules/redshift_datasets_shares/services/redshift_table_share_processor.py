import logging
from datetime import datetime
from typing import List
from dataall.base.utils.naming_convention import NamingConventionService, NamingConventionPattern
from dataall.modules.shares_base.services.sharing_service import ShareData
from dataall.modules.shares_base.services.share_processor_manager import SharesProcessorInterface
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_state_machines import ShareItemSM
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareItemStatus,
    ShareObjectActions,
    ShareItemActions,
)
from dataall.modules.redshift_datasets_shares.aws.redshift_data import redshift_share_data_client
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftTable
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository

log = logging.getLogger(__name__)

DATAALL_PREFIX = 'dataall'


class ProcessRedshiftShare(SharesProcessorInterface):
    def __init__(self, session, share_data, shareable_items, reapply=False):
        self.session = session
        self.share_data: ShareData = share_data
        self.dataset = share_data.dataset  # TODO verify it returns Redshift dataset
        self.share = share_data.share
        self.tables: List[RedshiftTable] = shareable_items
        self.reapply: bool = reapply

        dataset_connection = RedshiftConnectionRepository.get_redshift_connection(
            self.session, self.dataset.connectionUri
        )
        self.source_connection = dataset_connection
        # TODO: get admin connection for dataset namespace - might not be needed
        # self.source_connection = RedshiftConnectionRepository.get_redshift_connection(
        #     session=self.session,
        #     account_id=self.share_data.source_environment.AwsAccountId,
        #     region=self.share_data.source_environment.region,
        #     namespace=dataset_connection.namespaceId,
        # )
        # share.principalId = target connectionUri
        # share.principalRoleName = target redshift role
        self.target_connection = RedshiftConnectionRepository.get_redshift_connection(
            session, share_data.share.principalId
        )
        self.redshift_role = share_data.share.principalRoleName

        # There is a unique datashare per dataset per target namespace
        # To restrict pivot role permissions on the datashares both in source and target we prefix them with dataall prefix
        self.datashare_name = NamingConventionService(
            target_label=self.target_connection.namespaceId,
            pattern=NamingConventionPattern.REDSHIFT_DATASHARE,
            target_uri=self.dataset.datasetUri,
            resource_prefix=DATAALL_PREFIX,
        ).build_compliant_name()

    def process_approved_shares(self) -> bool:
        """
        1) (in source namespace) Create datashare for this dataset for this target namespace. If it does not exist yet. One time operation.
        2) (in source namespace) Add schema to the datashare, if not already added. One time operation.
        3) (in source namespace) Grant access to the consumer cluster to the datashare, if not already granted. One time operation.
        4) (in target namespace) Create local database from datashare, if it does not exist yet. One time operation.
        5) (in target namespace) Create external schema in local database, if it does not exist yet. One time operation.
        6) (in target namespace) Grant usage access to the redshift role to the schema.
        For each table:
            7) (in source namespace) Add table to the datashare, if not already added.
            8) (in target namespace) Grant select access to the requested table to the redshift role.
        Returns
        -------
        True if share is granted successfully
        """
        log.info('##### Starting Sharing Redshift tables #######')
        success = True
        if not self.tables:
            log.info('No Redshift tables to share. Skipping...')
        else:
            if not self.reapply:
                shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
                new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
                shared_item_SM.update_state(self.session, self.share.shareUri, new_state)
            try:
                redshift_client_in_source = redshift_share_data_client(
                    account_id=self.share_data.source_environment.AwsAccountId,
                    region=self.share_data.source_environment.region,
                    connection=self.source_connection,
                )
                redshift_client_in_target = redshift_share_data_client(
                    account_id=self.share_data.target_environment.AwsAccountId,
                    region=self.share_data.target_environment.region,
                    connection=self.target_connection,
                )

                # 1) Create datashare for this dataset for this target namespace. If it does not exist yet
                redshift_client_in_source.create_datashare(datashare=self.datashare_name)

                # 2) Add schema to the datashare, if not already added
                redshift_client_in_source.add_schema_to_datashare(
                    datashare=self.datashare_name, schema=self.dataset.schema
                )
                # 3) Grant access to the consumer cluster to the datashare, if not already granted
                redshift_client_in_source.grant_usage_to_datashare(
                    datashare=self.datashare_name, namespace=self.target_connection.namespaceId
                )

                # 4) Create local database from datashare, if it does not exist yet
                redshift_client_in_target.create_database_from_datashare(
                    database=self.dataset.name,
                    datashare=self.datashare_name,
                    namespace=self.source_connection.namespaceId,
                )
                # 5) Create external schema in local database, if it does not exist yet
                external_schema = redshift_client_in_target.create_external_schema(
                    database=self.dataset.name, schema=self.dataset.schema
                )
                # 6) Grant usage access to the redshift role to the schema.
                redshift_client_in_target.grant_schema_usage_access_to_redshift_role(
                    schema=external_schema, rs_role=self.redshift_role
                )

                for table in self.tables:
                    try:
                        # 7) Add tables to the datashare, if not already added
                        redshift_client_in_source.add_table_to_datashare(
                            datashare=self.datashare_name, schema=self.dataset.schema, table_name=table.name
                        )
                        # 8) Grant select access to the requested tables to the redshift role.
                        redshift_client_in_target.grant_select_table_access_to_redshift_role(
                            schema=external_schema, table=table, rs_role=self.redshift_role
                        )
                        share_item = ShareObjectRepository.find_sharable_item(
                            self.session, self.share.shareUri, table.rsTableUri
                        )
                        if not self.reapply:
                            table_SM = ShareItemSM(new_state)
                            final_state = table_SM.run_transition(ShareItemActions.Success.value)
                            table_SM.update_state_single_item(self.session, share_item, final_state)
                        ShareStatusRepository.update_share_item_health_status(
                            self.session, share_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                        )
                    except Exception as e:
                        log.error(
                            f'Failed to process approved redshift table {table} '
                            f'from source {self.source_connection=}'
                            f'with target {self.target_connection=}'
                            f'due to: {e}'
                        )
                        share_item = ShareObjectRepository.find_sharable_item(
                            self.session, self.share.shareUri, table.rsTableUri
                        )
                        if not self.reapply:
                            table_SM = ShareItemSM(new_state)
                            new_state = table_SM.run_transition(ShareItemActions.Failure.value)
                            table_SM.update_state_single_item(self.session, share_item, new_state)
                        else:
                            ShareStatusRepository.update_share_item_health_status(
                                self.session, share_item, ShareItemHealthStatus.Unhealthy.value, str(e), datetime.now()
                            )

            except Exception as e:
                log.error(
                    f'Failed to process approved redshift tables {self.tables} '
                    f'from source {self.source_connection=}'
                    f'with target {self.target_connection=}'
                    f'due to: {e}'
                )
                if not self.reapply:
                    new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                    shared_item_SM.update_state(self.session, self.share.shareUri, new_state)
                else:
                    for table in self.tables:
                        share_item = ShareObjectRepository.find_sharable_item(
                            self.session, self.share.shareUri, table.rsTableUri
                        )
                        ShareStatusRepository.update_share_item_health_status(
                            self.session, share_item, ShareItemHealthStatus.Unhealthy.value, str(e), datetime.now()
                        )
                return False
        return success

    def process_revoked_shares(self) -> bool:
        """
        For each table
            1) (in target namespace) Revoke access to the revoked tables to the redshift role
            2) (in source namespace) If that table is not shared in this namespace, remove table from datashare
        3) (in target namespace) If no more tables are shared with the redshift role, revoke usage access to the external schema to the redshift role
        4) (in target namespace) If no more tables are shared with any role in this namespace, drop local database
        5) (in source namespace) If no more tables are shared with any role in this namespace, drop datashare
        # Drop datashare deletes it from source and target, alongside its permissions.
        Returns
        -------
        True if share is revoked successfully
        """
        log.info('##### Starting Revoke Redshift tables #######')
        success = True
        if not self.tables:
            log.info('No Redshift tables to revoke. Skipping...')
        else:
            try:
                redshift_client_in_source = redshift_share_data_client(
                    account_id=self.share_data.source_environment.AwsAccountId,
                    region=self.share_data.source_environment.region,
                    connection=self.source_connection,
                )
                redshift_client_in_target = redshift_share_data_client(
                    account_id=self.share_data.target_environment.AwsAccountId,
                    region=self.share_data.target_environment.region,
                    connection=self.target_connection,
                )

                for table in self.tables:
                    log.info(f'Revoking access to table {table}...')
                    share_item = ShareObjectRepository.find_sharable_item(
                        self.session, self.share.shareUri, table.rsTableUri
                    )

                    revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
                    new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
                    revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

                    try:
                        # 1) (in target namespace) Revoke access to the revoked tables to the redshift role
                        redshift_client_in_target.revoke_select_table_access_to_redshift_role(
                            schema='placeholder', table=table, rs_role=self.redshift_role
                        )
                        # 2) (in source namespace) If that table is not shared in this namespace, remove table from datashare
                    except Exception as e:
                        log.error(
                            f'Failed to process revoked redshift table {table} '
                            f'from source {self.source_connection=}'
                            f'with target {self.target_connection=}'
                            f'due to: {e}'
                        )
                        share_item = ShareObjectRepository.find_sharable_item(
                            self.session, self.share.shareUri, table.rsTableUri
                        )
                        if not self.reapply:
                            table_SM = ShareItemSM(new_state)
                            new_state = table_SM.run_transition(ShareItemActions.Failure.value)
                            table_SM.update_state_single_item(self.session, share_item, new_state)
                        else:
                            ShareStatusRepository.update_share_item_health_status(
                                self.session, share_item, ShareItemHealthStatus.Unhealthy.value, str(e), datetime.now()
                            )
                # 3) (in target namespace) If no more tables are shared with the redshift role, revoke usage access to the external schema to the redshift role
                # 4) (in target namespace) If no more tables are shared with any role in this namespace, drop local database
                # 5) (in source namespace) If no more tables are shared with any role in this namespace, drop datashare

            except Exception as e:
                log.error(
                    f'Failed to process revoked redshift tables {self.tables} '
                    f'from source {self.source_connection=}'
                    f'with target {self.target_connection=}'
                    f'due to: {e}'
                )
                if not self.reapply:
                    new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                    revoked_item_SM.update_state(self.session, self.share.shareUri, new_state)
                else:
                    for table in self.tables:
                        share_item = ShareObjectRepository.find_sharable_item(
                            self.session, self.share.shareUri, table.rsTableUri
                        )
                        ShareStatusRepository.update_share_item_health_status(
                            self.session, share_item, ShareItemHealthStatus.Unhealthy.value, str(e), datetime.now()
                        )
                return False
            return success

    def verify_shares(self) -> bool:
        pass
