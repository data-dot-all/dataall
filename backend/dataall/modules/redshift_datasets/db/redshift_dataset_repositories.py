import logging

from sqlalchemy import or_, and_
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.base.db import paginate
from dataall.base.db.exceptions import ObjectNotFound
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset, RedshiftTable

logger = logging.getLogger(__name__)


class RedshiftDatasetEnvironmentResource(EnvironmentResource):
    """Actions performed on any environment resource on environment operations"""

    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return RedshiftDatasetRepository.count_environment_group_datasets(session, environment, group_uri)


class RedshiftDatasetRepository:
    """DAO layer for Redshift Datasets"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    @classmethod
    def create_redshift_dataset(cls, session, username, env: Environment, data: dict) -> RedshiftDataset:
        organization = OrganizationRepository.get_organization_by_uri(session, env.organizationUri)
        dataset = RedshiftDataset(
            label=data.get('label'),
            owner=username,
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            AwsAccountId=env.AwsAccountId,
            SamlAdminGroupName=data['SamlAdminGroupName'],
            region=env.region,
            environmentUri=env.environmentUri,
            organizationUri=env.organizationUri,
            language=data.get('language', Language.English.value),
            confidentiality=data.get('confidentiality', ConfidentialityClassification.Unclassified.value),
            topics=data.get('topics', []),
            businessOwnerEmail=data.get('businessOwnerEmail', ''),
            businessOwnerDelegationEmails=data.get('businessOwnerDelegationEmails', []),
            stewards=data.get('stewards') if data.get('stewards') else data['SamlAdminGroupName'],
            autoApprovalEnabled=data.get('autoApprovalEnabled', False),
            connectionUri=data.get('connectionUri'),
            schema=data.get('schema'),
        )
        session.add(dataset)
        session.commit()

        activity = Activity(
            action='redshift-dataset:import',
            label='redshift-dataset:import',
            owner=dataset.owner,
            summary=f'{dataset.owner} imported redshift dataset {dataset.name} in {env.name} on organization {organization.name}',
            targetUri=dataset.datasetUri,
            targetType='redshift-dataset',
        )
        session.add(activity)
        session.commit()
        return dataset

    @staticmethod
    def get_redshift_dataset_by_uri(session, dataset_uri) -> RedshiftDataset:
        dataset: RedshiftDataset = session.query(RedshiftDataset).get(dataset_uri)
        if not dataset:
            raise ObjectNotFound('RedshiftDataset', dataset_uri)
        return dataset

    @staticmethod
    def create_redshift_table(session, username, dataset_uri, data: dict) -> RedshiftTable:
        dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, dataset_uri)
        table = RedshiftTable(
            datasetUri=dataset.datasetUri,
            owner=username,
            name=data.get('name'),
            label=data.get('name'),
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            topics=data.get('topics', []),
        )
        session.add(table)
        session.commit()
        return table

    @staticmethod
    def get_redshift_table_by_uri(session, table_uri) -> RedshiftTable:
        table: RedshiftTable = session.query(RedshiftTable).get(table_uri)
        if not table:
            raise ObjectNotFound('RedshiftTable', table_uri)
        return table

    @staticmethod
    def _query_redshift_dataset_tables(session, dataset_uri, filter: dict = None):
        query = session.query(RedshiftTable).filter(RedshiftTable.datasetUri == dataset_uri)
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    *[
                        RedshiftTable.name.ilike('%' + filter.get('term') + '%'),
                        RedshiftTable.label.ilike('%' + filter.get('term') + '%'),
                    ]
                )
            )
        return query

    @staticmethod
    def list_redshift_dataset_tables(session, dataset_uri, filter: dict = None):
        query = RedshiftDatasetRepository._query_redshift_dataset_tables(session, dataset_uri, filter)
        return query.order_by(RedshiftTable.label).all()

    @staticmethod
    def paginated_redshift_dataset_tables(session, dataset_uri, data=None) -> dict:
        query = RedshiftDatasetRepository._query_redshift_dataset_tables(session, dataset_uri, data)
        return paginate(
            query=query,
            page_size=data.get('pageSize', RedshiftDatasetRepository._DEFAULT_PAGE_SIZE),
            page=data.get('page', RedshiftDatasetRepository._DEFAULT_PAGE),
        ).to_dict()

    @staticmethod
    def count_dataset_tables(session, dataset_uri) -> int:
        return RedshiftDatasetRepository._query_redshift_dataset_tables(session, dataset_uri).count()

    @staticmethod
    def count_environment_group_datasets(session, environment, group_uri) -> int:
        return (
            session.query(RedshiftDataset)
            .filter(
                and_(
                    RedshiftDataset.environmentUri == environment.environmentUri,
                    RedshiftDataset.SamlAdminGroupName == group_uri,
                )
            )
            .count()
        )
