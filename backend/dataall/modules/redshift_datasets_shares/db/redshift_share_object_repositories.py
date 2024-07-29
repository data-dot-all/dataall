import logging

from sqlalchemy import and_
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.shares_base.services.shares_enums import (
    ShareableType,
    PrincipalType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject

logger = logging.getLogger(__name__)


class RedshiftShareEnvironmentResource(EnvironmentResource):
    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        # TODO: get the environment group redshift role_uris, or redo logic
        return RedshiftShareObjectRepository.count_redshift_principal_shares(session, PrincipalType.RedshiftRole)

    @staticmethod
    def delete_env(session, environment):
        RedshiftShareObjectRepository.delete_all_redshift_share_items(session, environment.environmentUri)


class RedshiftShareObjectRepository:
    @staticmethod
    def count_redshift_principal_shares(session, principal_id: str, principal_type: PrincipalType):
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
                    ShareObjectItem.itemType == ShareableType.RedshiftTable.value,
                )
            )
            .count()
        )

    @staticmethod
    def delete_all_redshift_share_items(session, env_uri):
        env_shared_with_objects = session.query(ShareObject).filter(ShareObject.environmentUri == env_uri).all()
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
