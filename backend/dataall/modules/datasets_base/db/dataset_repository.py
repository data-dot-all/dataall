import logging

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from dataall.core.activity.db.activity_models import Activity
from dataall.core.catalog.db.glossary_models import TermLink, GlossaryNode
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization import Organization
from dataall.db import paginate
from dataall.db.exceptions import ObjectNotFound
from dataall.db.models.Enums import Language
from dataall.modules.datasets_base.db.enums import ConfidentialityClassification
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

logger = logging.getLogger(__name__)


class DatasetRepository(EnvironmentResource):
    """DAO layer for Datasets"""

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
            .filter(
                and_(
                    Dataset.environmentUri == environment.environmentUri,
                    Dataset.SamlAdminGroupName == group_uri
                ))
            .count()
        )

    @staticmethod
    def create_dataset(
        session,
        username: str,
        uri: str,
        data: dict = None,
    ) -> Dataset:
        environment = EnvironmentService.get_environment_by_uri(session, uri)

        organization = Organization.get_organization_by_uri(
            session, environment.organizationUri
        )

        dataset = Dataset(
            label=data.get('label'),
            owner=username,
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            AwsAccountId=environment.AwsAccountId,
            SamlAdminGroupName=data['SamlAdminGroupName'],
            region=environment.region,
            S3BucketName='undefined',
            GlueDatabaseName='undefined',
            IAMDatasetAdminRoleArn='undefined',
            IAMDatasetAdminUserArn='undefined',
            KmsAlias='undefined',
            environmentUri=environment.environmentUri,
            organizationUri=environment.organizationUri,
            language=data.get('language', Language.English.value),
            confidentiality=data.get(
                'confidentiality', ConfidentialityClassification.Unclassified.value
            ),
            topics=data.get('topics', []),
            businessOwnerEmail=data.get('businessOwnerEmail'),
            businessOwnerDelegationEmails=data.get('businessOwnerDelegationEmails', []),
            stewards=data.get('stewards')
            if data.get('stewards')
            else data['SamlAdminGroupName'],
        )
        session.add(dataset)
        session.commit()

        DatasetRepository._set_dataset_aws_resources(dataset, data, environment)
        DatasetRepository._set_import_data(dataset, data)

        activity = Activity(
            action='dataset:create',
            label='dataset:create',
            owner=username,
            summary=f'{username} created dataset {dataset.name} in {environment.name} on organization {organization.name}',
            targetUri=dataset.datasetUri,
            targetType='dataset',
        )
        session.add(activity)
        return dataset

    @staticmethod
    def _set_dataset_aws_resources(dataset: Dataset, data, environment):

        bucket_name = NamingConventionService(
            target_uri=dataset.datasetUri,
            target_label=dataset.label,
            pattern=NamingConventionPattern.S3,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()
        dataset.S3BucketName = data.get('bucketName') or bucket_name

        glue_db_name = NamingConventionService(
            target_uri=dataset.datasetUri,
            target_label=dataset.label,
            pattern=NamingConventionPattern.GLUE,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()
        dataset.GlueDatabaseName = data.get('glueDatabaseName') or glue_db_name

        kms_alias = bucket_name
        dataset.KmsAlias = data.get('KmsKeyId') or kms_alias

        iam_role_name = NamingConventionService(
            target_uri=dataset.datasetUri,
            target_label=dataset.label,
            pattern=NamingConventionPattern.IAM,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()
        iam_role_arn = f'arn:aws:iam::{dataset.AwsAccountId}:role/{iam_role_name}'
        if data.get('adminRoleName'):
            dataset.IAMDatasetAdminRoleArn = (
                f"arn:aws:iam::{dataset.AwsAccountId}:role/{data['adminRoleName']}"
            )
            dataset.IAMDatasetAdminUserArn = (
                f"arn:aws:iam::{dataset.AwsAccountId}:role/{data['adminRoleName']}"
            )
        else:
            dataset.IAMDatasetAdminRoleArn = iam_role_arn
            dataset.IAMDatasetAdminUserArn = iam_role_arn

        dataset.GlueCrawlerName = f'{dataset.S3BucketName}-{dataset.datasetUri}-crawler'
        dataset.GlueProfilingJobName = f'{dataset.S3BucketName}-{dataset.datasetUri}-profiler'
        dataset.GlueProfilingTriggerSchedule = None
        dataset.GlueProfilingTriggerName = f'{dataset.S3BucketName}-{dataset.datasetUri}-trigger'
        dataset.GlueDataQualityJobName = f'{dataset.S3BucketName}-{dataset.datasetUri}-dataquality'
        dataset.GlueDataQualitySchedule = None
        dataset.GlueDataQualityTriggerName = f'{dataset.S3BucketName}-{dataset.datasetUri}-dqtrigger'
        return dataset

    @staticmethod
    def paginated_dataset_tables(session, uri, data=None) -> dict:
        query = (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.datasetUri == uri,
                    DatasetTable.LastGlueTableStatus != 'Deleted',
                )
            )
            .order_by(DatasetTable.created.desc())
        )
        if data and data.get('term'):
            query = query.filter(
                or_(
                    *[
                        DatasetTable.name.ilike('%' + data.get('term') + '%'),
                        DatasetTable.GlueTableName.ilike(
                            '%' + data.get('term') + '%'
                        ),
                    ]
                )
            )
        return paginate(
            query=query, page_size=data.get('pageSize', 10), page=data.get('page', 1)
        ).to_dict()

    @staticmethod
    def update_dataset_activity(session, dataset, username) :
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
    def update_dataset_glossary_terms(session, username, uri, data):
        if data.get('terms'):
            input_terms = data.get('terms', [])
            current_links = session.query(TermLink).filter(
                TermLink.targetUri == uri
            )
            for current_link in current_links:
                if current_link not in input_terms:
                    session.delete(current_link)
            for nodeUri in input_terms:
                term = session.query(GlossaryNode).get(nodeUri)
                if term:
                    link = (
                        session.query(TermLink)
                        .filter(
                            TermLink.targetUri == uri,
                            TermLink.nodeUri == nodeUri,
                        )
                        .first()
                    )
                    if not link:
                        new_link = TermLink(
                            targetUri=uri,
                            nodeUri=nodeUri,
                            targetType='Dataset',
                            owner=username,
                            approvedByOwner=True,
                        )
                        session.add(new_link)

    @staticmethod
    def update_bucket_status(session, dataset_uri):
        """
        helper method to update the dataset bucket status
        """
        dataset = DatasetRepository.get_dataset_by_uri(session, dataset_uri)
        dataset.bucketCreated = True
        return dataset

    @staticmethod
    def update_glue_database_status(session, dataset_uri):
        """
        helper method to update the dataset db status
        """
        dataset = DatasetRepository.get_dataset_by_uri(session, dataset_uri)
        dataset.glueDatabaseCreated = True

    @staticmethod
    def get_dataset_tables(session, dataset_uri):
        """return the dataset tables"""
        return (
            session.query(DatasetTable)
            .filter(DatasetTable.datasetUri == dataset_uri)
            .all()
        )

    @staticmethod
    def delete_dataset(session, dataset) -> bool:
        session.delete(dataset)
        return True

    @staticmethod
    def delete_dataset_term_links(session, uri):
        tables = [t.tableUri for t in DatasetRepository.get_dataset_tables(session, uri)]
        for tableUri in tables:
            term_links = (
                session.query(TermLink)
                .filter(
                    and_(
                        TermLink.targetUri == tableUri,
                        TermLink.targetType == 'DatasetTable',
                    )
                )
                .all()
            )
            for link in term_links:
                session.delete(link)
                session.commit()
        term_links = (
            session.query(TermLink)
            .filter(
                and_(
                    TermLink.targetUri == uri,
                    TermLink.targetType == 'Dataset',
                )
            )
            .all()
        )
        for link in term_links:
            session.delete(link)

    @staticmethod
    def list_all_datasets(session) -> [Dataset]:
        return session.query(Dataset).all()

    @staticmethod
    def list_all_active_datasets(session) -> [Dataset]:
        return (
            session.query(Dataset).filter(Dataset.deleted.is_(None)).all()
        )

    @staticmethod
    def get_dataset_by_bucket_name(session, bucket) -> [Dataset]:
        return (
            session.query(Dataset)
            .filter(Dataset.S3BucketName == bucket)
            .first()
        )

    @staticmethod
    def count_dataset_tables(session, dataset_uri):
        return (
            session.query(DatasetTable)
            .filter(DatasetTable.datasetUri == dataset_uri)
            .count()
        )

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
    def paginated_environment_datasets(
            session, uri, data=None,
    ) -> dict:
        return paginate(
            query=DatasetRepository.query_environment_datasets(
                session, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def paginated_environment_group_datasets(
            session, env_uri, group_uri, data=None
    ) -> dict:
        return paginate(
            query=DatasetRepository.query_environment_group_datasets(
                session, env_uri, group_uri, data
            ),
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
    def _set_import_data(dataset, data):
        dataset.imported = True if data.get('imported') else False
        dataset.importedS3Bucket = True if data.get('bucketName') else False
        dataset.importedGlueDatabase = True if data.get('glueDatabaseName') else False
        dataset.importedKmsKey = True if data.get('KmsKeyId') else False
        dataset.importedAdminRole = True if data.get('adminRoleName') else False
