import logging
from sqlalchemy import and_

from dataall.base.db import exceptions
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.services.shares_enums import ShareableType, ShareableTypeUri

logger = logging.getLogger(__name__)


class ShareObjectRepository:  # TODO: Slowly moving db models and repositories to shares_base, Then we can break down the single ShareObjectRepository into smaller repos
    @staticmethod
    def get_share_by_uri(session, uri):
        share = session.query(ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)
        return share

    @staticmethod
    def update_share_object_status(session, share_uri: str, status: str) -> ShareObject:
        share = ShareObjectRepository.get_share_by_uri(session, share_uri)
        share.status = status
        session.commit()
        return share

    @staticmethod
    def update_share_item_status(
        session,
        uri: str,
        status: str,
    ) -> ShareObjectItem:
        share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
        share_item.status = status
        session.commit()
        return share_item

    @staticmethod
    def delete_share_item_status_batch(
        session,
        share_uri: str,
        status: str,
    ):
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == status))
            .delete()
        )

    @staticmethod
    def update_share_item_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.status == old_status))
            .update(
                {
                    ShareObjectItem.status: new_status,
                }
            )
        )
        return True


    @staticmethod
    def get_share_data(session, share_uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, share_uri)
        dataset: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)

        source_environment: Environment = session.query(Environment).get(dataset.environmentUri)
        if not source_environment:
            raise exceptions.ObjectNotFound('SourceEnvironment', dataset.environmentUri)

        target_environment: Environment = session.query(Environment).get(share.environmentUri)
        if not target_environment:
            raise exceptions.ObjectNotFound('TargetEnvironment', share.environmentUri)

        env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == share.environmentUri,
                    EnvironmentGroup.groupUri == share.groupUri,
                )
            )
            .first()
        )
        if not env_group:
            raise Exception(
                f'Share object Team {share.groupUri} is not a member of the '
                f'environment {target_environment.name}/{target_environment.AwsAccountId}'
            )

        source_env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == dataset.environmentUri,
                    EnvironmentGroup.groupUri == dataset.SamlAdminGroupName,
                )
            )
            .first()
        )
        if not source_env_group:
            raise Exception(
                f'Share object Team {dataset.SamlAdminGroupName} is not a member of the '
                f'environment {dataset.environmentUri}'
            )

        return (
            source_env_group,
            env_group,
            dataset,
            share,
            source_environment,
            target_environment,
        )

    @staticmethod
    def get_share_data_items(session, share_uri, status=None, healthStatus=None):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, share_uri)
        items = {}
        for type in ShareableType:
            items[type.value] = ShareObjectRepository._find_all_share_item(
                session, share, status, healthStatus, type.value, ShareableTypeUri[type.value].value
            )
        return items

    @staticmethod
    def _find_all_share_item(session, share, status, healthStatus, share_type_model, share_type_uri):
        query = (
            session.query(share_type_model)
            .join(
                ShareObjectItem,
                ShareObjectItem.itemUri == share_type_uri,
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.datasetUri == share.datasetUri,
                    ShareObject.environmentUri == share.environmentUri,
                    ShareObject.shareUri == share.shareUri,
                )
            )
        )
        if status:
            query = query.filter(ShareObjectItem.status == status)
        if healthStatus:
            query = query.filter(ShareObjectItem.healthStatus == healthStatus)
        return query.all()

    @staticmethod
    def find_sharable_item(session, share_uri, item_uri) -> ShareObjectItem:
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.shareUri == share_uri,
                )
            )
            .first()
        )

    @staticmethod
    def get_all_shareable_items(session, share_uri, status=None, healthStatus=None):
        shared_items_dict = ShareObjectRepository.get_share_data_items(session, share_uri, status, healthStatus)
        uris = []
        uris.extend([item.itemUri for item in list(shared_items_dict.values())])
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri.in_(uris),
                    ShareObjectItem.shareUri == share_uri,
                )
            )
            .all()
        )

    @staticmethod
    def list_all_active_share_objects(session) -> [ShareObject]:
        return session.query(ShareObject).filter(ShareObject.deleted.is_(None)).all()

    @staticmethod
    def update_share_item_health_status_batch(
        session,
        share_uri: str,
        old_status: str,
        new_status: str,
    ) -> bool:
        (
            session.query(ShareObjectItem)
            .filter(and_(ShareObjectItem.shareUri == share_uri, ShareObjectItem.healthStatus == old_status))
            .update(
                {
                    ShareObjectItem.healthStatus: new_status,
                }
            )
        )
        return True