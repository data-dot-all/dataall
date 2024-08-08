import logging

from sqlalchemy import and_
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.shares_base.services.shares_enums import (
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
            .join(
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
    def _query_other_shares_redshift_table_with_connection(session, share_uri: str, table_uri: str, namespace_id: str):
        """Query all SHARED shares for a table with a namespace as target besides the one passed"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObject.shareUri != share_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObjectItem.itemUri == table_uri,
                    ShareObject.principalId == namespace_id,
                )
            )
        )
        return query.order_by(ShareObject.created)

    @staticmethod
    def count_other_shares_redshift_table_with_connection(
        session, share_uri: str, table_uri: str, namespace_id: str
    ) -> int:
        return RedshiftShareRepository._query_other_shares_redshift_table_with_connection(
            session, share_uri, table_uri, namespace_id
        ).count()

    @staticmethod
    def _query_shares_with_redshift_role(session, dataset_uri: str, rs_role: str, namespace_id: str):
        """Query all SHARED shares of a dataset for a redshift role"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.principalRoleName == rs_role,
                    ShareObject.principalId == namespace_id,
                )
            )
        )
        return query.order_by(ShareObject.created)

    @staticmethod
    def count_shares_with_redshift_role(session, dataset_uri: str, rs_role: str, namespace_id: str) -> int:
        return RedshiftShareRepository._query_shares_with_redshift_role(
            session, dataset_uri, rs_role, namespace_id
        ).count()

    @staticmethod
    def _query_shares_with_namespace(session, dataset_uri: str, rs_role: str, namespace_id: str):
        """Query all SHARED shares of a dataset for a namespace"""
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObjectItem.shareUri == ShareObject.shareUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.principalRoleName == rs_role,
                    ShareObject.principalId == namespace_id,
                )
            )
        )
        return query.order_by(ShareObject.created)

    @staticmethod
    def count_shares_with_namespace(session, dataset_uri: str, rs_role: str, namespace_id: str) -> int:
        return RedshiftShareRepository._query_shares_with_redshift_role(
            session, dataset_uri, rs_role, namespace_id
        ).count()
