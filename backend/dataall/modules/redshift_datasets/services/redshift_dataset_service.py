import logging

from dataall.base.context import get_context
from dataall.base.utils.naming_convention import NamingConventionService, NamingConventionPattern
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.vote.db.vote_repositories import VoteRepository

from dataall.modules.datasets_base.services.datasets_enums import DatasetRole

from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import (
    MANAGE_REDSHIFT_DATASETS,
    IMPORT_REDSHIFT_DATASET,
    GET_REDSHIFT_DATASET,
    RETRY_REDSHIFT_DATASHARE,
    REDSHIFT_DATASET_ALL,
    REDSHIFT_DATASET_READ,
)
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset
from dataall.modules.redshift_datasets.api.connections.enums import RedshiftType
from dataall.modules.redshift_datasets.aws.redshift import Redshift


log = logging.getLogger(__name__)


class RedshiftDatasetService:
    @staticmethod
    #@TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    #@ResourcePolicyService.has_resource_permission(IMPORT_REDSHIFT_DATASET)
    #@GroupPolicyService.has_group_permission(IMPORT_REDSHIFT_DATASET)
    def import_redshift_dataset(uri, admin_group, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            dataset = RedshiftDatasetRepository.create_redshift_dataset(
                session=session, username=context.username, env=environment, data=data
            )
            connection = RedshiftConnectionRepository.find_redshift_connection(session, dataset.connectionUri)
            datashare_name = NamingConventionService(
                target_label=dataset.label,
                pattern=NamingConventionPattern.REDSHIFT_DATASHARE,
                target_uri=dataset.datasetUri,
                resource_prefix=environment.resourcePrefix
            ).build_compliant_name()
            dataset.datashareArn = f'arn:aws:redshift:{dataset.region}:{dataset.AwsAccountId}:datashare:{connection.nameSpaceId if connection.redshiftType == RedshiftType.Serverless.value else connection.clusterId}/{datashare_name}'
            dataset.userRoleForDataset = DatasetRole.Creator.value
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=REDSHIFT_DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=RedshiftDataset.__name__,
            )
            if dataset.stewards and dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    permissions=REDSHIFT_DATASET_READ,
                    resource_uri=dataset.datasetUri,
                    resource_type=RedshiftDataset.__name__,
                )

            if environment.SamlGroupName != dataset.SamlAdminGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=REDSHIFT_DATASET_ALL,
                    resource_uri=dataset.datasetUri,
                    resource_type=RedshiftDataset.__name__,
                )
            # DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri) #TODO: UNCOMMENT

            for table in data.get('tables', []):
                RedshiftDatasetRepository.create_redshift_table(
                    session=session,
                    username=context.username,
                    dataset_uri=dataset.datasetUri,
                    data={'name': table},
                )

            task = Task(
                targetUri=dataset.datasetUri,
                action='redshift.datashare.import',
                payload={},
            )
            session.add(task)
            session.commit()
            Worker.queue(engine=context.db_engine, task_ids=[task.taskUri])

        return dataset

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def get_redshift_dataset(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            if dataset.SamlAdminGroupName in context.groups:
                dataset.userRoleForDataset = DatasetRole.Admin.value
            return dataset

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(RETRY_REDSHIFT_DATASHARE)
    def retry_redshift_datashare(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            return Redshift(account_id=dataset.AwsAccountId, region=dataset.region).describe_datashare_status(
                dataset.datashareArn
            )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def list_redshift_dataset_tables(uri, filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            return RedshiftDatasetRepository.paginated_redshift_dataset_tables(
                session=session,
                dataset_uri=dataset.datasetUri,
                data=filter
            )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def get_datashare_status(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            return Redshift(account_id=dataset.AwsAccountId, region=dataset.region).describe_datashare_status(
                dataset.datashareArn
            )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def get_dataset_upvotes(uri):
        with get_context().db_engine.scoped_session() as session:
            return VoteRepository.count_upvotes(session, uri, target_type='redshift-dataset') or 0
