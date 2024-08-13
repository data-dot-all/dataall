import logging

from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObjectItemDataFilter
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.base.db import exceptions

logger = logging.getLogger(__name__)


class ShareObjectItemRepository:
    @staticmethod
    def get_share_item_filter_by_uri(session, attached_filter_uri):
        item_data_filter: ShareObjectItemDataFilter = session.query(ShareObjectItemDataFilter).get(attached_filter_uri)
        if not item_data_filter:
            raise exceptions.ObjectNotFound('ShareObjectItemDataFilter', attached_filter_uri)
        return item_data_filter

    @staticmethod
    def count_all_share_item_filters_with_data_filter_uri(session, filter_uri):
        return (
            session.query(ShareObjectItemDataFilter)
            .filter(
                ShareObjectItemDataFilter.dataFilterUris.contains(f'{{{filter_uri}}}'),
            )
            .count()
        )

    @staticmethod
    def get_share_item_by_item_filter_uri(session, uri):
        return session.query(ShareObjectItem).filter(ShareObjectItem.attachedDataFilterUri == uri).first()

    @staticmethod
    def delete_share_item_filter(session, share_item_filter) -> None:
        session.delete(share_item_filter)

    @staticmethod
    def update_share_item_filter(
        session,
        share_item_filter: ShareObjectItemDataFilter,
        data: dict,
    ) -> ShareObjectItemDataFilter:
        share_item_filter.label = data.get('label')
        share_item_filter.dataFilterUris = data.get('filterUris')
        share_item_filter.dataFilterNames = data.get('filterNames')
        session.commit()
        return share_item_filter

    @staticmethod
    def create_share_item_filter(
        session,
        share_item: ShareObjectItem,
        data: dict,
    ) -> ShareObjectItemDataFilter:
        share_item_data_filter = ShareObjectItemDataFilter(
            label=data.get('label'),
            itemUri=share_item.itemUri,
            dataFilterUris=data.get('filterUris'),
            dataFilterNames=data.get('filterNames'),
        )
        session.add(share_item_data_filter)
        session.commit()
        return share_item_data_filter

    @staticmethod
    def delete_all_share_item_filters(session, item_uri):
        session.query(ShareObjectItemDataFilter).filter(ShareObjectItemDataFilter.itemUri == item_uri).delete()

    @staticmethod
    def delete_share_item_filters_with_data_filter_uri(session, filter_uri):
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        return (
            session.query(ShareObjectItemDataFilter)
            .filter(
                ShareObjectItemDataFilter.dataFilterUris.contains(f'{{{filter_uri}}}'),
            )
            .delete()
        )
