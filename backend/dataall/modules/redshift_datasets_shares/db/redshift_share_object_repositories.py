import logging

from sqlalchemy import and_
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemStatus,
    ShareableType,
    PrincipalType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository

logger = logging.getLogger(__name__)


class RedshiftShareEnvironmentResource(EnvironmentResource):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return RedshiftShareRepository.count_redshift_principal_shares(
            session=session, environment_uri=environment.environmentUri, group_uri=group_uri
        )

    @staticmethod
    def delete_env(session, environment):
        RedshiftShareRepository.delete_all_redshift_share_items(session, environment.environmentUri)


class RedshiftShareRepository:
    @staticmethod
    def count_redshift_principal_shares(session, environment_uri: str, group_uri: str):
        """
        Count RedshiftTables currently shared with Redshift Roles for a particular
        environment on behalf of a particular group
        """
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        return (
            session.query(ShareObject)
            .outerjoin(
                ShareObjectItem,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.environmentUri == environment_uri,
                    ShareObject.groupUri == group_uri,
                    ShareObject.principalType == PrincipalType.RedshiftRole.value,
                    ShareObjectItem.itemType == ShareableType.RedshiftTable.value,
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .count()
        )

    @staticmethod
    def delete_all_redshift_share_items(session, env_uri):
        """
        Delete all ShareObjects and ShareObjectItems of Redshift type for a particular environment
        """
        env_shared_with_objects = (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.environmentUri == env_uri, ShareObject.principalType == PrincipalType.RedshiftRole.value
                )
            )
            .all()
        )
        for share in env_shared_with_objects:
            (
                session.query(ShareObjectItem)
                .filter(
                    and_(
                        ShareObjectItem.shareUri == share.shareUri,
                        ShareObjectItem.itemType == ShareableType.RedshiftTable.value,
                    ),
                )
                .delete()
            )
            session.delete(share)

    @staticmethod
    def _query_other_shared_items_redshift_table_with_connection(
        session, share_uri: str, table_uri: str, connection_uri: str
    ):
        """Query all SHARED shares - Revoke_In_Progress for a table with a namespace as target besides the one passed"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        share_item_shared_states.remove(ShareItemStatus.Revoke_In_Progress.value)
        query = (
            session.query(ShareObjectItem)
            .outerjoin(
                ShareObject,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.shareUri != share_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObjectItem.itemUri == table_uri,
                    ShareObject.principalId == connection_uri,
                )
            )
        )
        return query.order_by(ShareObject.created)

    @staticmethod
    def count_other_shared_items_redshift_table_with_connection(
        session, share_uri: str, table_uri: str, connection_uri: str
    ) -> int:
        return RedshiftShareRepository._query_other_shared_items_redshift_table_with_connection(
            session, share_uri, table_uri, connection_uri
        ).count()

    @staticmethod
    def _query_dataset_shared_items_with_redshift_role(session, dataset_uri: str, rs_role: str, connection_uri: str):
        """Query all SHARED items - Revoke_In_Progress of a dataset for a redshift role"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        share_item_shared_states.remove(ShareItemStatus.Revoke_In_Progress.value)
        query = (
            session.query(ShareObjectItem)
            .outerjoin(ShareObject, ShareObject.shareUri == ShareObjectItem.shareUri)
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.principalRoleName == rs_role,
                    ShareObject.principalId == connection_uri,
                )
            )
        )
        return query.order_by(ShareObject.created)

    @staticmethod
    def count_dataset_shared_items_with_redshift_role(
        session, dataset_uri: str, rs_role: str, connection_uri: str
    ) -> int:
        return RedshiftShareRepository._query_dataset_shared_items_with_redshift_role(
            session, dataset_uri, rs_role, connection_uri
        ).count()

    @staticmethod
    def _query_dataset_shared_items_with_namespace(session, dataset_uri: str, connection_uri: str):
        """Query all SHARED shares - Revoke_In_Progress of a dataset for a namespace"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        share_item_shared_states.remove(ShareItemStatus.Revoke_In_Progress.value)
        query = (
            session.query(ShareObjectItem)
            .outerjoin(ShareObject, ShareObject.shareUri == ShareObjectItem.shareUri)
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.principalId == connection_uri,
                )
            )
        )
        return query.order_by(ShareObject.created)

    @staticmethod
    def count_dataset_shared_items_with_namespace(session, dataset_uri: str, connection_uri: str) -> int:
        return RedshiftShareRepository._query_dataset_shared_items_with_namespace(
            session, dataset_uri, connection_uri
        ).count()
