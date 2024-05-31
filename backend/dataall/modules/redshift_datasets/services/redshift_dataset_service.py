import logging

from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService

from dataall.modules.datasets_base.services.datasets_enums import DatasetRole

from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import (
    MANAGE_REDSHIFT_DATASETS,
    IMPORT_REDSHIFT_DATASET,
    REDSHIFT_DATASET_ALL,
    REDSHIFT_DATASET_READ,
)
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset


log = logging.getLogger(__name__)


class RedshiftDatasetService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(IMPORT_REDSHIFT_DATASET)
    @GroupPolicyService.has_group_permission(IMPORT_REDSHIFT_DATASET)
    def import_redshift_dataset(uri, admin_group, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            dataset = RedshiftDatasetRepository.create_redshift_dataset(
                session=session, username=context.username, env=environment, data=data
            )
            #TODO: ADD LOGIC TO CREATE REDSHIFT DATASHARE

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

            # DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri)

        dataset.userRoleForDataset = DatasetRole.Creator.value

        return dataset
