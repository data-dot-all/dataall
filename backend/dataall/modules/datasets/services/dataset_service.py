import logging
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from dataall.core.context import get_context
from dataall.core.permission_checker import has_tenant_permission, has_resource_permission
from dataall.db.api import (
    Environment,
    ResourcePolicy,
    KeyValueTag,
    Vote,
    Stack,
    has_tenant_perm,
    has_resource_perm,
)
from dataall.db.api import Organization
from dataall.db import models, api, exceptions, paginate, permissions
from dataall.db.models.Enums import Language, ConfidentialityClassification
from dataall.modules.datasets.db.dataset_repository import DatasetRepository
from dataall.modules.datasets.db.models import DatasetTable, Dataset
from dataall.modules.datasets.services.dataset_location_service import DatasetLocationService
from dataall.modules.datasets.services.dataset_permissions import MANAGE_DATASETS, UPDATE_DATASET, DATASET_READ, \
    DATASET_ALL, DATASET_TABLE_READ, LIST_ENVIRONMENT_DATASETS, CREATE_DATASET
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

logger = logging.getLogger(__name__)


class DatasetService:
    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(CREATE_DATASET)
    def create_dataset(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> Dataset:
        if not uri:
            raise exceptions.RequiredParameter('environmentUri')
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('SamlAdminGroupName'):
            raise exceptions.RequiredParameter('group')
        if not data.get('label'):
            raise exceptions.RequiredParameter('label')
        if len(data['label']) > 52:
            raise exceptions.InvalidInput(
                'Dataset name', data['label'], 'less than 52 characters'
            )

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data['SamlAdminGroupName'],
            permission_name=CREATE_DATASET,
        )

        environment = Environment.get_environment_by_uri(session, uri)

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

        DatasetService._set_dataset_aws_resources(dataset, data, environment)

        activity = models.Activity(
            action='dataset:create',
            label='dataset:create',
            owner=username,
            summary=f'{username} created dataset {dataset.name} in {environment.name} on organization {organization.name}',
            targetUri=dataset.datasetUri,
            targetType='dataset',
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['SamlAdminGroupName'],
            permissions=DATASET_ALL,
            resource_uri=dataset.datasetUri,
            resource_type=Dataset.__name__,
        )
        if dataset.stewards and dataset.stewards != dataset.SamlAdminGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.stewards,
                permissions=DATASET_READ,
                resource_uri=dataset.datasetUri,
                resource_type=Dataset.__name__,
            )
        if environment.SamlGroupName != dataset.SamlAdminGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=Dataset.__name__,
            )
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
    def create_dataset_stack(session, dataset: Dataset) -> models.Stack:
        return Stack.create_stack(
            session=session,
            environment_uri=dataset.environmentUri,
            target_uri=dataset.datasetUri,
            target_label=dataset.label,
            target_type='dataset',
            payload={
                'bucket_name': dataset.S3BucketName,
                'database_name': dataset.GlueDatabaseName,
                'role_name': dataset.S3BucketName,
                'user_name': dataset.S3BucketName,
            },
        )

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    def get_dataset(session, uri: str) -> Dataset:
        return DatasetService.get_dataset_by_uri(session, uri)

    @staticmethod
    def get_dataset_by_uri(session, dataset_uri) -> Dataset:
        return DatasetRepository.get_dataset_by_uri(session, dataset_uri)

    @staticmethod
    def query_user_datasets(session, username, groups, filter) -> Query:
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        query = (
            session.query(Dataset)
            .outerjoin(
                models.ShareObject,
                models.ShareObject.datasetUri == Dataset.datasetUri,
            )
            .outerjoin(
                models.ShareObjectItem,
                models.ShareObjectItem.shareUri == models.ShareObject.shareUri
            )
            .filter(
                or_(
                    Dataset.owner == username,
                    Dataset.SamlAdminGroupName.in_(groups),
                    Dataset.stewards.in_(groups),
                    and_(
                        models.ShareObject.principalId.in_(groups),
                        models.ShareObjectItem.status.in_(share_item_shared_states),
                    ),
                    and_(
                        models.ShareObject.owner == username,
                        models.ShareObjectItem.status.in_(share_item_shared_states),
                    ),
                )
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    Dataset.description.ilike(filter.get('term') + '%%'),
                    Dataset.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_datasets(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=DatasetService.query_user_datasets(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def paginated_dataset_tables(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
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
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET)
    def update_dataset(session, uri, data=None) -> Dataset:
        username = get_context().username
        dataset: Dataset = DatasetService.get_dataset_by_uri(session, uri)
        if data and isinstance(data, dict):
            for k in data.keys():
                if k != 'stewards':
                    setattr(dataset, k, data.get(k))
            if data.get('stewards') and data.get('stewards') != dataset.stewards:
                if data.get('stewards') != dataset.SamlAdminGroupName:
                    DatasetService.transfer_stewardship_to_new_stewards(
                        session, dataset, data['stewards']
                    )
                    dataset.stewards = data['stewards']
                else:
                    DatasetService.transfer_stewardship_to_owners(session, dataset)
                    dataset.stewards = dataset.SamlAdminGroupName

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=Dataset.__name__,
            )
            DatasetService.update_dataset_glossary_terms(session, username, uri, data)
            activity = models.Activity(
                action='dataset:update',
                label='dataset:update',
                owner=username,
                summary=f'{username} updated dataset {dataset.name}',
                targetUri=dataset.datasetUri,
                targetType='dataset',
            )
            session.add(activity)
            session.commit()
        return dataset

    @staticmethod
    def transfer_stewardship_to_owners(session, dataset):
        dataset_shares = (
            session.query(models.ShareObject)
            .filter(models.ShareObject.datasetUri == dataset.datasetUri)
            .all()
        )
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    permissions=permissions.SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=models.ShareObject.__name__,
                )
        return dataset

    @staticmethod
    def transfer_stewardship_to_new_stewards(session, dataset, new_stewards):
        env = Environment.get_environment_by_uri(session, dataset.environmentUri)
        if dataset.stewards != env.SamlGroupName:
            ResourcePolicy.delete_resource_policy(
                session=session,
                group=dataset.stewards,
                resource_uri=dataset.datasetUri,
            )
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=new_stewards,
            permissions=DATASET_READ,
            resource_uri=dataset.datasetUri,
            resource_type=Dataset.__name__,
        )

        dataset_tables = [t.tableUri for t in DatasetService.get_dataset_tables(session, dataset.datasetUri)]
        for tableUri in dataset_tables:
            if dataset.stewards != env.SamlGroupName:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=tableUri,
                )
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=new_stewards,
                permissions=DATASET_TABLE_READ,
                resource_uri=tableUri,
                resource_type=DatasetTable.__name__,
            )

        dataset_shares = (
            session.query(models.ShareObject)
            .filter(models.ShareObject.datasetUri == dataset.datasetUri)
            .all()
        )
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=new_stewards,
                    permissions=permissions.SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=models.ShareObject.__name__,
                )
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=share.shareUri,
                )
        return dataset

    @staticmethod
    def update_dataset_glossary_terms(session, username, uri, data):
        if data.get('terms'):
            input_terms = data.get('terms', [])
            current_links = session.query(models.TermLink).filter(
                models.TermLink.targetUri == uri
            )
            for current_link in current_links:
                if current_link not in input_terms:
                    session.delete(current_link)
            for nodeUri in input_terms:
                term = session.query(models.GlossaryNode).get(nodeUri)
                if term:
                    link = (
                        session.query(models.TermLink)
                        .filter(
                            models.TermLink.targetUri == uri,
                            models.TermLink.nodeUri == nodeUri,
                        )
                        .first()
                    )
                    if not link:
                        new_link = models.TermLink(
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
        dataset = DatasetService.get_dataset_by_uri(session, dataset_uri)
        dataset.bucketCreated = True
        return dataset

    @staticmethod
    def update_glue_database_status(session, dataset_uri):
        """
        helper method to update the dataset db status
        """
        dataset = DatasetService.get_dataset_by_uri(session, dataset_uri)
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
    def query_dataset_shares(session, dataset_uri) -> Query:
        return session.query(models.ShareObject).filter(
            and_(
                models.ShareObject.datasetUri == dataset_uri,
                models.ShareObject.deleted.is_(None),
            )
        )

    @staticmethod
    def paginated_dataset_shares(
        session, username, groups, uri, data=None, check_perm=None
    ) -> [models.ShareObject]:
        query = DatasetService.query_dataset_shares(session, uri)
        return paginate(
            query=query, page=data.get('page', 1), page_size=data.get('pageSize', 5)
        ).to_dict()

    @staticmethod
    def list_dataset_shares(session, dataset_uri) -> [models.ShareObject]:
        """return the dataset shares"""
        query = DatasetService.query_dataset_shares(session, dataset_uri)
        return query.all()

    @staticmethod
    def list_dataset_shares_with_existing_shared_items(session, dataset_uri) -> [models.ShareObject]:
        query = session.query(models.ShareObject).filter(
            and_(
                models.ShareObject.datasetUri == dataset_uri,
                models.ShareObject.deleted.is_(None),
                models.ShareObject.existingSharedItems.is_(True),
            )
        )
        return query.all()

    @staticmethod
    def list_dataset_redshift_clusters(
        session, dataset_uri
    ) -> [models.RedshiftClusterDataset]:
        """return the dataset clusters"""
        return (
            session.query(models.RedshiftClusterDataset)
            .filter(models.RedshiftClusterDataset.datasetUri == dataset_uri)
            .all()
        )

    @staticmethod
    def delete_dataset(
        session, username, groups, uri, data=None, check_perm=None
    ) -> bool:
        dataset = DatasetService.get_dataset_by_uri(session, uri)
        DatasetService._delete_dataset_shares_with_no_shared_items(session, uri)
        DatasetService._delete_dataset_term_links(session, uri)
        DatasetService._delete_dataset_tables(session, dataset.datasetUri)
        DatasetLocationService.delete_dataset_locations(session, dataset.datasetUri)
        KeyValueTag.delete_key_value_tags(session, dataset.datasetUri, 'dataset')
        Vote.delete_votes(session, dataset.datasetUri, 'dataset')
        session.delete(dataset)
        ResourcePolicy.delete_resource_policy(
            session=session, resource_uri=uri, group=dataset.SamlAdminGroupName
        )
        env = Environment.get_environment_by_uri(session, dataset.environmentUri)
        if dataset.SamlAdminGroupName != env.SamlGroupName:
            ResourcePolicy.delete_resource_policy(
                session=session, resource_uri=uri, group=env.SamlGroupName
            )
        if dataset.stewards:
            ResourcePolicy.delete_resource_policy(
                session=session, resource_uri=uri, group=dataset.stewards
            )
        return True

    @staticmethod
    def _delete_dataset_shares_with_no_shared_items(session, dataset_uri):
        share_objects = (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.ShareObject.datasetUri == dataset_uri,
                    models.ShareObject.existingSharedItems.is_(False),
                )
            )
            .all()
        )
        for share in share_objects:
            (
                session.query(models.ShareObjectItem)
                .filter(models.ShareObjectItem.shareUri == share.shareUri)
                .delete()
            )
            session.delete(share)

    @staticmethod
    def _delete_dataset_term_links(session, uri):
        tables = [t.tableUri for t in DatasetService.get_dataset_tables(session, uri)]
        for tableUri in tables:
            term_links = (
                session.query(models.TermLink)
                .filter(
                    and_(
                        models.TermLink.targetUri == tableUri,
                        models.TermLink.targetType == 'DatasetTable',
                    )
                )
                .all()
            )
            for link in term_links:
                session.delete(link)
                session.commit()
        term_links = (
            session.query(models.TermLink)
            .filter(
                and_(
                    models.TermLink.targetUri == uri,
                    models.TermLink.targetType == 'Dataset',
                )
            )
            .all()
        )
        for link in term_links:
            session.delete(link)

    @staticmethod
    def _delete_dataset_tables(session, dataset_uri) -> bool:
        tables = (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.datasetUri == dataset_uri,
                )
            )
            .all()
        )
        for table in tables:
            table.deleted = datetime.now()
        return tables

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
    def query_environment_group_datasets(session, envUri, groupUri, filter) -> Query:
        query = session.query(Dataset).filter(
            and_(
                Dataset.environmentUri == envUri,
                Dataset.SamlAdminGroupName == groupUri,
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
    @has_resource_permission(LIST_ENVIRONMENT_DATASETS)
    def paginated_environment_datasets(
            session, uri, data=None,
    ) -> dict:
        return paginate(
            query=DatasetService.query_environment_datasets(
                session, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def paginated_environment_group_datasets(
            session, envUri, groupUri, data=None
    ) -> dict:
        return paginate(
            query=DatasetService.query_environment_group_datasets(
                session, envUri, groupUri, data
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
