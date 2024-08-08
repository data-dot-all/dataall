import logging
from typing import List

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectStatus,
    ShareableType,
    PrincipalType,
)
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject, ShareObjectItemDataFilter
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, S3Dataset
from dataall.modules.datasets_base.db.dataset_models import DatasetBase

logger = logging.getLogger(__name__)


class S3ShareEnvironmentResource(EnvironmentResource):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return S3ShareObjectRepository.count_S3_principal_shares(
            session, group_uri, environment.environmentUri, PrincipalType.Group
        )

    @staticmethod
    def count_role_resources(session, role_uri):
        return S3ShareObjectRepository.count_S3_role_principal_shares(session, role_uri, PrincipalType.ConsumptionRole)

    @staticmethod
    def delete_env(session, environment):
        S3ShareObjectRepository.delete_all_S3_share_items(session, environment.environmentUri)


class S3ShareObjectRepository:
    @staticmethod
    def count_S3_principal_shares(session, principal_id: str, environment_uri: str, principal_type: PrincipalType):
        return (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.principalId == principal_id,
                    ShareObject.principalType == principal_type.value,
                    ShareObject.environmentUri == environment_uri,
                    ShareObjectItem.itemType.in_(
                        [ShareableType.Table.value, ShareableType.S3Bucket.value, ShareableType.StorageLocation.value]
                    ),
                )
            )
            .count()
        )

    @staticmethod
    def count_S3_role_principal_shares(session, principal_id: str, principal_type: PrincipalType):
        return (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.principalId == principal_id,
                    ShareObject.principalType == principal_type.value,
                    ShareObjectItem.itemType.in_(
                        [ShareableType.Table.value, ShareableType.S3Bucket.value, ShareableType.StorageLocation.value]
                    ),
                )
            )
            .count()
        )

    @staticmethod
    def delete_all_S3_share_items(session, env_uri):
        env_shared_with_objects = session.query(ShareObject).filter(ShareObject.environmentUri == env_uri).all()
        for share in env_shared_with_objects:
            (
                session.query(ShareObjectItem)
                .filter(
                    and_(
                        ShareObjectItem.shareUri == share.shareUri,
                        ShareObjectItem.itemType.in_(
                            [
                                ShareableType.Table.value,
                                ShareableType.S3Bucket.value,
                                ShareableType.StorageLocation.value,
                            ]
                        ),
                    )
                )
                .delete(synchronize_session=False)
            )
            session.delete(share)

    @staticmethod
    def find_all_other_share_items(
        session, not_this_share_uri, item_uri, share_type, principal_type, principal_uri, item_status=None
    ) -> List[ShareObjectItem]:
        """
        Find all shares from principal (principal_uri) to item (item_uri), that are not from specified share (not_this_share_uri)
        """
        query = (
            session.query(ShareObjectItem)
            .join(ShareObject, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                (
                    and_(
                        ShareObjectItem.itemUri == item_uri,
                        ShareObjectItem.itemType == share_type,
                        ShareObject.principalType == principal_type,
                        ShareObject.principalId == principal_uri,
                        ShareObject.shareUri != not_this_share_uri,
                    )
                )
            )
        )
        if item_status:
            query = query.filter(ShareObjectItem.status.in_(item_status))
        return query.all()

    @staticmethod
    def list_user_s3_shared_datasets(session, username, groups) -> Query:
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        query = (
            session.query(DatasetBase)
            .outerjoin(
                ShareObject,
                ShareObject.datasetUri == DatasetBase.datasetUri,
            )
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    or_(
                        ShareObject.principalId.in_(groups),
                        ShareObject.owner == username,
                    ),
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObjectItem.itemType.in_(
                        [ShareableType.Table.value, ShareableType.S3Bucket.value, ShareableType.StorageLocation.value]
                    ),
                )
            )
        )
        return query.distinct(DatasetBase.datasetUri)

    @staticmethod
    def get_share_by_dataset_attributes(session, dataset_uri, dataset_owner, groups=[]):
        share: ShareObject = (
            session.query(ShareObject)
            .filter(ShareObject.datasetUri == dataset_uri)
            .filter(or_(ShareObject.owner == dataset_owner, ShareObject.principalId.in_(groups)))
            .first()
        )
        return share

    @staticmethod
    def check_other_approved_share_item_table_exists(session, environment_uri, item_uri, share_item_uri):
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.environmentUri == environment_uri,
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.itemType == ShareableType.Table.value,
                    ShareObjectItem.shareItemUri != share_item_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
        )
        return query.first()

    @staticmethod
    def check_existing_shared_items_of_type(session, uri, item_type):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, uri)
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        shared_items = (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    ShareObjectItem.itemType == item_type,
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .all()
        )
        if shared_items:
            return True
        return False

    @staticmethod
    def query_dataset_tables_shared_with_env(
        session, environment_uri: str, dataset_uri: str, username: str, groups: [str]
    ):
        """For a given dataset, returns the list of Tables shared with the environment
        This means looking at approved ShareObject items
        for the share object associating the dataset and environment
        """
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        env_tables_shared_query = (
            session.query(
                DatasetTable.tableUri.label('tableUri'),
                DatasetTable.GlueTableName.label('GlueTableName'),
                ShareObjectItemDataFilter.label.label('resourceLinkSuffix'),
            )
            .join(
                ShareObjectItem,
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                ShareObjectItemDataFilter,
                ShareObjectItemDataFilter.attachedDataFilterUri == ShareObjectItem.attachedDataFilterUri,
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.environmentUri == environment_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.principalType != PrincipalType.ConsumptionRole.value,
                    or_(
                        ShareObject.owner == username,
                        ShareObject.principalId.in_(groups),
                    ),
                )
            )
        )
        return env_tables_shared_query.all()

    @staticmethod
    def query_shared_glue_databases(session, groups, env_uri, group_uri):
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        q = (
            session.query(
                ShareObjectItem.shareUri.label('shareUri'),
                S3Dataset.datasetUri.label('datasetUri'),
                S3Dataset.name.label('datasetName'),
                S3Dataset.name.label('sharedGlueDatabaseName'),
                Environment.environmentUri.label('environmentUri'),
                Environment.name.label('environmentName'),
                Environment.AwsAccountId.label('targetEnvAwsAccountId'),
                Environment.region.label('targetEnvRegion'),
                ShareObject.created.label('created'),
                ShareObject.principalId.label('principalId'),
                ShareObject.principalType.label('principalType'),
                ShareObject.environmentUri.label('targetEnvironmentUri'),
                ShareObjectItem.itemType.label('itemType'),
                ShareObjectItem.itemName.label('itemName'),
                S3Dataset.GlueDatabaseName.label('GlueDatabaseName'),
                DatasetTable.GlueTableName.label('GlueTableName'),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                S3Dataset,
                ShareObject.datasetUri == S3Dataset.datasetUri,
            )
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .outerjoin(
                DatasetTable,
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.environmentUri == env_uri,
                    ShareObject.principalId == group_uri,
                    ShareObject.groupUri.in_(groups),
                    ShareObjectItem.itemType == ShareableType.Table.value,
                )
            )
        )
        return q.order_by(ShareObject.shareUri).distinct(ShareObject.shareUri).all()

    @staticmethod
    def check_existing_s3_shared_items(session, item_uri: str) -> int:
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObjectItem.itemType.in_(
                        [ShareableType.Table.value, ShareableType.S3Bucket.value, ShareableType.StorageLocation.value]
                    ),
                )
            )
            .count()
        )

    @staticmethod
    def delete_s3_share_item(session, item_uri: str):
        session.query(ShareObjectItem).filter(ShareObjectItem.itemUri == item_uri).delete()

    @staticmethod
    def delete_s3_shares_with_no_shared_items(session, dataset_uri):
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        shares = (
            session.query(ShareObject)
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObjectItem.status.notin_(share_item_shared_states),
                )
            )
            .all()
        )
        for share in shares:
            share_items = session.query(ShareObjectItem).filter(ShareObjectItem.shareUri == share.shareUri).all()
            for item in share_items:
                session.delete(item)

            share_obj = session.query(ShareObject).filter(ShareObject.shareUri == share.shareUri).first()
            session.delete(share_obj)

    @staticmethod
    def find_s3_dataset_shares(session, dataset_uri):
        return session.query(ShareObject).filter(ShareObject.datasetUri == dataset_uri).all()

    @staticmethod
    def list_s3_dataset_shares_with_existing_shared_items(
        session, dataset_uri, environment_uri=None, item_type=None
    ) -> [ShareObject]:
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.deleted.is_(None),
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
        )
        if environment_uri:
            query = query.filter(ShareObject.environmentUri == environment_uri)
        if item_type:
            query = query.filter(ShareObjectItem.itemType == item_type)
        return query.all()

    # the next 2 methods are used in subscription task
    @staticmethod
    def find_share_items_by_item_uri(session, item_uri):
        return session.query(ShareObjectItem).filter(ShareObjectItem.itemUri == item_uri).all()

    @staticmethod
    def get_approved_share_object(session, item):
        share_object: ShareObject = (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.shareUri == item.shareUri,
                    ShareObject.status == ShareObjectStatus.Approved.value,
                )
            )
            .first()
        )
        return share_object
