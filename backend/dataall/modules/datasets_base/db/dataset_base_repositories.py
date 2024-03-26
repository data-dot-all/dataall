import logging
from sqlalchemy import and_, or_
from sqlalchemy.orm import Query
from dataall.core.activity.db.activity_models import Activity
from dataall.base.db import paginate
from dataall.base.db.exceptions import ObjectNotFound
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.datasets_base.db.dataset_base_models import Dataset, DatasetLock

logger = logging.getLogger(__name__)


class DatasetBaseRepository(EnvironmentResource):
    """DAO layer for GENERIC Datasets"""


    @staticmethod
    def get_dataset_by_uri(session, dataset_uri) -> Dataset:
        dataset: Dataset = session.query(Dataset).get(dataset_uri)
        if not dataset:
            raise ObjectNotFound('Dataset', dataset_uri)
        return dataset

    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return (
            session.query(Dataset)
            .filter(and_(Dataset.environmentUri == environment.environmentUri, Dataset.SamlAdminGroupName == group_uri))
            .count()
        )

    @staticmethod
    def create_dataset_lock(session, dataset: Dataset):
        dataset_lock = DatasetLock(datasetUri=dataset.datasetUri, isLocked=False, acquiredBy='')
        session.add(dataset_lock)
        session.commit()

    @staticmethod
    def delete_dataset_lock(session, dataset: Dataset):
        dataset_lock = session.query(DatasetLock).filter(DatasetLock.datasetUri == dataset.datasetUri).first()
        session.delete(dataset_lock)
        session.commit()

    @staticmethod
    def update_dataset_activity(session, dataset, username):
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

    @staticmethod
    def delete_dataset(session, dataset) -> bool:
        session.delete(dataset)
        return True

    @staticmethod
    def list_all_datasets(session) -> [Dataset]:
        return session.query(Dataset).all()

    @staticmethod
    def list_all_active_datasets(session) -> [Dataset]:
        return session.query(Dataset).filter(Dataset.deleted.is_(None)).all()


    @staticmethod
    def query_environment_group_datasets(session, env_uri, group_uri, filter) -> Query:
        query = session.query(Dataset).filter(
            and_(
                Dataset.environmentUri == env_uri,
                Dataset.SamlAdminGroupName == group_uri,
                Dataset.deleted.is_(None),
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    Dataset.label.ilike('%' + term + '%'),
                    Dataset.description.ilike('%' + term + '%'),
                    Dataset.tags.contains(f'{{{term}}}'),
                    Dataset.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    def query_environment_datasets(session, uri, filter) -> Query:
        query = session.query(Dataset).filter(
            and_(
                Dataset.environmentUri == uri,
                Dataset.deleted.is_(None),
            )
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    Dataset.label.ilike('%' + term + '%'),
                    Dataset.description.ilike('%' + term + '%'),
                    Dataset.tags.contains(f'{{{term}}}'),
                    Dataset.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    def query_environment_imported_datasets(session, uri, filter) -> Query:
        query = session.query(Dataset).filter(
            and_(Dataset.environmentUri == uri, Dataset.deleted.is_(None), Dataset.imported.is_(True))
        )
        if filter and filter.get('term'):
            term = filter['term']
            query = query.filter(
                or_(
                    Dataset.label.ilike('%' + term + '%'),
                    Dataset.description.ilike('%' + term + '%'),
                    Dataset.tags.contains(f'{{{term}}}'),
                    Dataset.region.ilike('%' + term + '%'),
                )
            )
        return query

    @staticmethod
    def paginated_environment_datasets(
        session,
        uri,
        data=None,
    ) -> dict:
        return paginate(
            query=DatasetBaseRepository.query_environment_datasets(session, uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def paginated_environment_group_datasets(session, env_uri, group_uri, data=None) -> dict:
        return paginate(
            query=DatasetBaseRepository.query_environment_group_datasets(session, env_uri, group_uri, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def list_group_datasets(session, environment_id, group_uri):
        return (
            session.query(Dataset)
            .filter(
                and_(
                    Dataset.environmentUri == environment_id,
                    Dataset.SamlAdminGroupName == group_uri,
                )
            )
            .all()
        )

    @staticmethod
    def paginated_user_datasets(session, username, groups, data=None) -> dict:
        return paginate(
            query=DatasetBaseRepository._query_user_datasets(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def _query_user_datasets(session, username, groups, filter) -> Query:
        query = session.query(Dataset).filter(
            or_(
                Dataset.owner == username,
                Dataset.SamlAdminGroupName.in_(groups),
                Dataset.stewards.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    Dataset.description.ilike(filter.get('term') + '%%'),
                    Dataset.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.distinct(Dataset.datasetUri)
