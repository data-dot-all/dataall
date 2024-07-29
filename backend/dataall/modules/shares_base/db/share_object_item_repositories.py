import logging
from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Query
from typing import List

from dataall.base.db import exceptions, paginate
from dataall.base.db.paginator import Page
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.notifications.db.notification_models import Notification
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject, ShareObjectItemDataFilter

from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    PrincipalType,
)

logger = logging.getLogger(__name__)


class ShareObjectItemRepository:
    @staticmethod
    def get_share_item_filter_by_uri(session, attached_filter_uri):
        return (
            session.query(ShareObjectItemDataFilter)
            .filter(ShareObjectItemDataFilter.attachedDataFilterUri == attached_filter_uri)
            .first()
        )

    @staticmethod
    def get_share_item_by_item_filter_uri(session, uri):
        return session.query(ShareObjectItem).filter(ShareObjectItem.attachedDataFilterUri == uri).first()

    @staticmethod
    def delete_share_item_filter(session, share_item_filter) -> bool:
        session.delete(share_item_filter)

    @staticmethod
    def update_share_item_filters(
        session,
        share_item_filter: ShareObjectItemDataFilter,
        data: dict,
    ) -> bool:
        share_item_filter.label = data.get('label')
        share_item_filter.dataFilterUris = data.get('dataFilterUris')
        share_item_filter.dataFilterNames = data.get('dataFilterNames')
        session.commit()
        return share_item_filter

    @staticmethod
    def create_share_item_filters(
        session,
        share_item: str,
        data: dict,
    ) -> bool:
        share_item_data_filter = ShareObjectItemDataFilter(
            label=data.get('label'),
            dataFilterUris=data.get('dataFilterUris'),
            dataFilterNames=data.get('dataFilterNames'),
        )
        session.add(share_item_data_filter)
        session.commit()
        return share_item_data_filter

    @staticmethod
    def find_share_item_filter(session, item_uri, attached_filter_uri) -> ShareObjectItem:
        return (
            session.query(ShareObjectItemDataFilter)
            .filter(
                ShareObjectItemDataFilter.itemUri == item_uri,
                ShareObjectItemDataFilter.attachedDataFilterUri == attached_filter_uri,
            )
            .first()
        )
