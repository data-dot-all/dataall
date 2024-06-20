import logging

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.shares_base.services.shares_enums import (
    ShareableType,
    ShareItemStatus,
)
from dataall.modules.s3_datasets_shares.aws.glue_client import GlueClient
from dataall.modules.s3_datasets_shares.db.share_object_repositories import S3ShareObjectRepository
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetStorageLocation
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_TABLE_READ, DATASET_FOLDER_READ

log = logging.getLogger(__name__)


class S3ShareItemService:
    @staticmethod
    def get_glue_database_for_share(glueDatabase, account_id, region):  # TODO: IN S3_DATASETS_SHARES
        # Check if a catalog account exists and return database accordingly
        try:
            catalog_dict = GlueClient(
                account_id=account_id,
                region=region,
                database=glueDatabase,
            ).get_source_catalog()

            if catalog_dict is not None:
                return catalog_dict.get('database_name')
            else:
                return glueDatabase
        except Exception as e:
            raise e

    @staticmethod
    def delete_dataset_table_read_permission(session, share, tableUri):
        """
        Delete Table permissions to share groups
        """
        other_shares = S3ShareObjectRepository.list_other_shares_for_item(
            session,
            not_this_share_uri=share.shareUri,
            item_uri=tableUri,
            share_type=ShareableType.Table.value,
            principal_type='GROUP',
            principal_uri=share.groupUri,
            item_status=[ShareItemStatus.Share_Succeeded.value],
        )
        log.info(f'Table {tableUri} has been shared with group {share.groupUri} in {len(other_shares)} more shares')
        if len(other_shares) == 0:
            log.info('Delete permissions...')
            ResourcePolicyService.delete_resource_policy(session=session, group=share.groupUri, resource_uri=tableUri)

    @staticmethod
    def delete_dataset_folder_read_permission(session, share, locationUri):
        """
        Delete Folder permissions to share groups
        """
        other_shares = S3ShareObjectRepository.list_other_shares_for_item(
            session,
            not_this_share_uri=share.shareUri,
            item_uri=locationUri,
            share_type=ShareableType.StorageLocation.value,
            principal_type='GROUP',
            principal_uri=share.groupUri,
            item_status=[ShareItemStatus.Share_Succeeded.value],
        )
        log.info(
            f'Location {locationUri} has been shared with group {share.groupUri} in {len(other_shares)} more shares'
        )
        if len(other_shares) == 0:
            log.info('Delete permissions...')
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=share.groupUri,
                resource_uri=locationUri,
            )

    @staticmethod
    def attach_dataset_table_read_permission(session, share, tableUri):
        """
        Attach Table permissions to share groups
        """
        existing_policy = ResourcePolicyService.find_resource_policies(
            session,
            group=share.groupUri,
            resource_uri=tableUri,
            resource_type=DatasetTable.__name__,
            permissions=DATASET_TABLE_READ,
        )
        # toDo: separate policies from list DATASET_TABLE_READ, because in future only one of them can be granted (Now they are always granted together)
        if len(existing_policy) == 0:
            log.info(
                f'Attaching new resource permission policy {DATASET_TABLE_READ} to table {tableUri} for group {share.groupUri}'
            )
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.groupUri,
                permissions=DATASET_TABLE_READ,
                resource_uri=tableUri,
                resource_type=DatasetTable.__name__,
            )
        else:
            log.info(
                f'Resource permission policy {DATASET_TABLE_READ} to table {tableUri} for group {share.groupUri} already exists. Skip... '
            )

    @staticmethod
    def attach_dataset_folder_read_permission(session, share, locationUri):
        """
        Attach Folder permissions to share groups
        """
        existing_policy = ResourcePolicyService.find_resource_policies(
            session,
            group=share.groupUri,
            resource_uri=locationUri,
            resource_type=DatasetStorageLocation.__name__,
            permissions=DATASET_FOLDER_READ,
        )
        # toDo: separate policies from list DATASET_TABLE_READ, because in future only one of them can be granted (Now they are always granted together)
        if len(existing_policy) == 0:
            log.info(
                f'Attaching new resource permission policy {DATASET_FOLDER_READ} to folder {locationUri} for group {share.groupUri}'
            )

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.groupUri,
                permissions=DATASET_FOLDER_READ,
                resource_uri=locationUri,
                resource_type=DatasetStorageLocation.__name__,
            )
        else:
            log.info(
                f'Resource permission policy {DATASET_FOLDER_READ} to table {locationUri} for group {share.groupUri} already exists. Skip... '
            )
