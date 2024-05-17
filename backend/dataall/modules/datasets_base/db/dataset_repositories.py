import logging
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query
from dataall.base.db import paginate
from dataall.core.activity.db.activity_models import Activity
from dataall.modules.datasets_base.db.dataset_models import DatasetBase, DatasetLock

logger = logging.getLogger(__name__)


class DatasetBaseRepository:
    """DAO layer for GENERIC Datasets"""

    @staticmethod
    def create_dataset_lock(session, dataset: DatasetBase):
        dataset_lock = DatasetLock(datasetUri=dataset.datasetUri, isLocked=False, acquiredBy='')
        session.add(dataset_lock)
        session.commit()

    @staticmethod
    def delete_dataset_lock(session, dataset: DatasetBase):
        dataset_lock = session.query(DatasetLock).filter(DatasetLock.datasetUri == dataset.datasetUri).first()
        session.delete(dataset_lock)
        session.commit()

    @staticmethod
    def update_dataset_activity(session, dataset: DatasetBase, username):
        activity = Activity(
            action='dataset:update',
            label='dataset:update',
            owner=username,
            summary=f'{username} updated dataset {dataset.name}',
            targetUri=dataset.datasetUri,
            targetType='dataset',
        )
        session.add(activity)
        session.commit()


class DatasetListRepository:
    """DAO layer for Listing Datasets in Environments"""

    @staticmethod
    def paginated_all_user_datasets(session, username, groups, all_subqueries, data=None) -> dict:
        return paginate(
            query=DatasetListRepository._query_all_user_datasets(session, username, groups, all_subqueries, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def _query_all_user_datasets(session, username, groups, all_subqueries, filter) -> Query:
        query = session.query(DatasetBase).filter(
            or_(
                DatasetBase.owner == username,
                DatasetBase.SamlAdminGroupName.in_(groups),
                DatasetBase.stewards.in_(groups),
            )
        )
        if query.first() is not None:
            all_subqueries.append(query)
        if len(all_subqueries) == 1:
            query = all_subqueries[0]
        elif len(all_subqueries) > 1:
            query = all_subqueries[0].union(*all_subqueries[1:])

        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    DatasetBase.description.ilike(filter.get('term') + '%%'),
                    DatasetBase.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(DatasetBase.label).distinct(DatasetBase.datasetUri, DatasetBase.label)

    @staticmethod
    def paginated_user_datasets(session, username, groups, data=None) -> dict:
        return paginate(
            query=DatasetListRepository._query_user_datasets(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def _query_user_datasets(session, username, groups, filter) -> Query:
        query = session.query(DatasetBase).filter(
            or_(
                DatasetBase.owner == username,
                DatasetBase.SamlAdminGroupName.in_(groups),
                DatasetBase.stewards.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    DatasetBase.description.ilike(filter.get('term') + '%%'),
                    DatasetBase.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(DatasetBase.label).distinct(DatasetBase.datasetUri, DatasetBase.label)

    @staticmethod
    def paginated_environment_datasets(
        session,
        uri,
        data=None,
    ) -> dict:
        return paginate(
            query=DatasetListRepository._query_environment_datasets(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def _query_environment_datasets(session, uri, filter) -> Query:
        query = session.query(DatasetBase).filter(
            and_(
                DatasetBase.environmentUri == uri,
                DatasetBase.deleted.is_(None),
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    DatasetBase.label.ilike('%' + term + '%'),
                    DatasetBase.description.ilike('%' + term + '%'),
                    DatasetBase.tags.contains(f'{{{term}}}'),
                    DatasetBase.region.ilike('%' + term + '%'),
                )
            )
        return query.order_by(DatasetBase.label)
