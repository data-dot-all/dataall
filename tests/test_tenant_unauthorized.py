import inspect
import logging
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
from typing import Mapping
from unittest.mock import MagicMock, patch, ANY

import pytest
from assertpy import assert_that

from dataall.base.api import bootstrap
from dataall.base.context import RequestContext
from dataall.base.db.exceptions import TenantUnauthorized, ResourceUnauthorized
from dataall.core.permissions.services.environment_permissions import GET_ENVIRONMENT
from dataall.core.permissions.services.network_permissions import GET_NETWORK
from dataall.core.permissions.services.organization_permissions import GET_ORGANIZATION
from dataall.core.permissions.services.tenant_permissions import MANAGE_ENVIRONMENTS, MANAGE_ORGANIZATIONS
from dataall.modules.catalog.services.glossaries_permissions import MANAGE_GLOSSARIES
from dataall.modules.dashboards.services.dashboard_permissions import MANAGE_DASHBOARDS, SHARE_DASHBOARD
from dataall.modules.datapipelines.services.datapipelines_permissions import GET_PIPELINE, MANAGE_PIPELINES
from dataall.modules.metadata_forms.services.metadata_form_permissions import MANAGE_METADATA_FORMS
from dataall.modules.mlstudio.services.mlstudio_permissions import GET_SGMSTUDIO_USER, MANAGE_SGMSTUDIO_USERS
from dataall.modules.notebooks.services.notebook_permissions import GET_NOTEBOOK, MANAGE_NOTEBOOKS
from dataall.modules.omics.services.omics_permissions import MANAGE_OMICS_RUNS
from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import MANAGE_REDSHIFT_DATASETS
from dataall.modules.s3_datasets.services.dataset_permissions import GET_DATASET, GET_DATASET_TABLE, MANAGE_DATASETS
from dataall.modules.shares_base.services.share_permissions import MANAGE_SHARES
from dataall.modules.worksheets.services.worksheet_permissions import MANAGE_WORKSHEETS


class IgnoreReason(Enum):
    TENANT = 'admin action. No need for tenant permission check'
    APPSUPPORT = 'permissions do not apply to application support features'
    BACKPORT = 'outside of this PR to be able to backport to v2.6.2'
    INTRAMODULE = 'returns intra-module data'
    USERROLEINRESOURCE = 'checks user permissions for a particular feature'
    PUBLIC = 'public by design'
    SIMPLIFIED = 'simplified response'
    USERLIMITED = 'returns user resources in application'
    CUSTOM = 'custom permissions checks'
    ADMINLIMITED = 'limited to resource owners/admin'
    NOTREQUIRED = 'permission check is not required'


def field_id(type_name: str, field_name: str) -> str:
    return f'{type_name}_{field_name}'


@dataclass
class TestData:
    resource_ignore: IgnoreReason = None
    resource_perm: str = None
    tenant_ignore: IgnoreReason = None
    tenant_perm: str = None

    def __post_init__(self):
        if not bool(self.resource_perm) ^ bool(self.resource_ignore):
            raise ValueError('Either resource_perm or resource_ignore must be set')
        if not bool(self.tenant_perm) ^ bool(self.tenant_ignore):
            raise ValueError('Either tenant_perm or tenant_ignore must be set')


EXPECTED_RESOLVERS: Mapping[str, TestData] = {
    field_id('AttachedMetadataForm', 'entityName'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('AttachedMetadataForm', 'fields'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('AttachedMetadataForm', 'metadataForm'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('AttachedMetadataFormField', 'field'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('AttachedMetadataFormField', 'hasTenantPermissions'): TestData(
        resource_ignore=IgnoreReason.USERROLEINRESOURCE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Category', 'associations'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Category', 'categories'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Category', 'children'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Category', 'stats'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Category', 'terms'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ConsumptionRole', 'managedPolicies'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dashboard', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dashboard', 'terms'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dashboard', 'upvotes'): TestData(
        resource_ignore=IgnoreReason.APPSUPPORT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dashboard', 'userRoleForDashboard'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DataPipeline', 'cloneUrlHttp'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DataPipeline', 'developmentEnvironments'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DataPipeline', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DataPipeline', 'organization'): TestData(
        resource_perm=GET_ORGANIZATION, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DataPipeline', 'stack'): TestData(resource_perm=GET_PIPELINE, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('DataPipeline', 'userRoleForPipeline'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dataset', 'environment'): TestData(resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Dataset', 'locations'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dataset', 'owners'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dataset', 'stack'): TestData(resource_perm=GET_DATASET, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Dataset', 'statistics'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dataset', 'stewards'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dataset', 'tables'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Dataset', 'terms'): TestData(resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Dataset', 'userRoleForDataset'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetBase', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetBase', 'owners'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetBase', 'stack'): TestData(resource_perm=GET_DATASET, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('DatasetBase', 'stewards'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetBase', 'userRoleForDataset'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetProfilingRun', 'dataset'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetProfilingRun', 'results'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetProfilingRun', 'status'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetStorageLocation', 'dataset'): TestData(
        resource_perm=GET_DATASET, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetStorageLocation', 'terms'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetTable', 'GlueTableProperties'): TestData(
        resource_perm=GET_DATASET_TABLE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetTable', 'columns'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetTable', 'dataset'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetTable', 'terms'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('DatasetTableColumn', 'terms'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Environment', 'networks'): TestData(resource_perm=GET_NETWORK, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Environment', 'organization'): TestData(
        resource_ignore=IgnoreReason.SIMPLIFIED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Environment', 'parameters'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Environment', 'stack'): TestData(resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Environment', 'userRoleInEnvironment'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('EnvironmentSimplified', 'networks'): TestData(
        resource_perm=GET_NETWORK, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('EnvironmentSimplified', 'organization'): TestData(
        resource_ignore=IgnoreReason.SIMPLIFIED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Feed', 'messages'): TestData(
        resource_ignore=IgnoreReason.APPSUPPORT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Glossary', 'associations'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Glossary', 'categories'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Glossary', 'children'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Glossary', 'stats'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Glossary', 'tree'): TestData(resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Glossary', 'userRoleForGlossary'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('GlossaryTermLink', 'target'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('GlossaryTermLink', 'term'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Group', 'environmentPermissions'): TestData(
        resource_ignore=IgnoreReason.USERROLEINRESOURCE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Group', 'tenantPermissions'): TestData(
        resource_ignore=IgnoreReason.USERROLEINRESOURCE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('MetadataForm', 'fields'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('MetadataForm', 'homeEntityName'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('MetadataForm', 'userRole'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('MetadataFormField', 'glossaryNodeName'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('MetadataFormSearchResult', 'hasTenantPermissions'): TestData(
        resource_ignore=IgnoreReason.USERROLEINRESOURCE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'DisableDataSubscriptions'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'addConnectionGroupPermission'): TestData(
        tenant_ignore=IgnoreReason.BACKPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'addConsumptionRoleToEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'addRedshiftDatasetTables'): TestData(
        tenant_perm=MANAGE_REDSHIFT_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'addSharedItem'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'approveDashboardShare'): TestData(
        tenant_perm=MANAGE_DASHBOARDS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'approveShareExtension'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'approveShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'approveTermAssociation'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'archiveOrganization'): TestData(
        tenant_perm=MANAGE_ORGANIZATIONS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'batchMetadataFormFieldUpdates'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'cancelShareExtension'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createAttachedMetadataForm'): TestData(
        tenant_ignore=IgnoreReason.BACKPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createCategory'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createDataPipeline'): TestData(
        tenant_perm=MANAGE_PIPELINES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createDataPipelineEnvironment'): TestData(
        tenant_perm=MANAGE_PIPELINES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createDataset'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createDatasetStorageLocation'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createGlossary'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createMetadataForm'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createMetadataFormFields'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createMetadataFormVersion'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createNetwork'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createOmicsRun'): TestData(
        tenant_perm=MANAGE_OMICS_RUNS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createOrganization'): TestData(
        tenant_perm=MANAGE_ORGANIZATIONS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createQuicksightDataSourceSet'): TestData(
        tenant_ignore=IgnoreReason.TENANT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createRedshiftConnection'): TestData(
        tenant_ignore=IgnoreReason.BACKPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createSagemakerNotebook'): TestData(
        tenant_perm=MANAGE_NOTEBOOKS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createSagemakerStudioUser'): TestData(
        tenant_perm=MANAGE_SGMSTUDIO_USERS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createTableDataFilter'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createTerm'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'createWorksheet'): TestData(
        tenant_perm=MANAGE_WORKSHEETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteAttachedMetadataForm'): TestData(
        tenant_ignore=IgnoreReason.BACKPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteCategory'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteConnectionGroupPermission'): TestData(
        tenant_ignore=IgnoreReason.BACKPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteDashboard'): TestData(
        tenant_perm=MANAGE_DASHBOARDS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteDataPipeline'): TestData(
        tenant_perm=MANAGE_PIPELINES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteDataPipelineEnvironment'): TestData(
        tenant_perm=MANAGE_PIPELINES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteDataset'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteDatasetStorageLocation'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteDatasetTable'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteGlossary'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteMetadataForm'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteMetadataFormField'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteMetadataFormVersion'): TestData(
        tenant_perm=MANAGE_METADATA_FORMS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteNetwork'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteNotification'): TestData(
        tenant_ignore=IgnoreReason.APPSUPPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteOmicsRun'): TestData(
        tenant_perm=MANAGE_OMICS_RUNS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteRedshiftConnection'): TestData(
        tenant_ignore=IgnoreReason.BACKPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteRedshiftDataset'): TestData(
        tenant_perm=MANAGE_REDSHIFT_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteRedshiftDatasetTable'): TestData(
        tenant_perm=MANAGE_REDSHIFT_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteSagemakerNotebook'): TestData(
        tenant_perm=MANAGE_NOTEBOOKS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteSagemakerStudioUser'): TestData(
        tenant_perm=MANAGE_SGMSTUDIO_USERS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteTableDataFilter'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteTerm'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'deleteWorksheet'): TestData(
        tenant_perm=MANAGE_WORKSHEETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'dismissTermAssociation'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'enableDataSubscriptions'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'generateDatasetAccessToken'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'importDashboard'): TestData(
        tenant_perm=MANAGE_DASHBOARDS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'importDataset'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'importRedshiftDataset'): TestData(
        tenant_perm=MANAGE_REDSHIFT_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'inviteGroupOnEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'inviteGroupToOrganization'): TestData(
        tenant_perm=MANAGE_ORGANIZATIONS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'markNotificationAsRead'): TestData(
        tenant_ignore=IgnoreReason.APPSUPPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'postFeedMessage'): TestData(
        tenant_ignore=IgnoreReason.APPSUPPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'reApplyItemsShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'reApplyShareObjectItemsOnDataset'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'rejectDashboardShare'): TestData(
        tenant_perm=MANAGE_DASHBOARDS, resource_perm=SHARE_DASHBOARD
    ),
    field_id('Mutation', 'rejectShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'removeConsumptionRoleFromEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'removeGroupFromEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'removeGroupFromOrganization'): TestData(
        tenant_perm=MANAGE_ORGANIZATIONS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'removeShareItemFilter'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'removeSharedItem'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'requestDashboardShare'): TestData(
        tenant_perm=MANAGE_DASHBOARDS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'revokeItemsShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'startDatasetProfilingRun'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'startGlueCrawler'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'startMaintenanceWindow'): TestData(
        tenant_ignore=IgnoreReason.TENANT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'startReindexCatalog'): TestData(
        tenant_ignore=IgnoreReason.TENANT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'startSagemakerNotebook'): TestData(
        tenant_perm=MANAGE_NOTEBOOKS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'stopMaintenanceWindow'): TestData(
        tenant_ignore=IgnoreReason.TENANT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'stopSagemakerNotebook'): TestData(
        tenant_perm=MANAGE_NOTEBOOKS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'submitShareExtension'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'submitShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'syncDatasetTableColumns'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'syncTables'): TestData(tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED),
    field_id('Mutation', 'upVote'): TestData(
        tenant_ignore=IgnoreReason.APPSUPPORT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateCategory'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateConsumptionRole'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDashboard'): TestData(
        tenant_perm=MANAGE_DASHBOARDS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDataPipeline'): TestData(
        tenant_perm=MANAGE_PIPELINES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDataPipelineEnvironment'): TestData(
        tenant_perm=MANAGE_PIPELINES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDataset'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDatasetStorageLocation'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDatasetTable'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateDatasetTableColumn'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateEnvironment'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateGlossary'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateGroupEnvironmentPermissions'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateGroupTenantPermissions'): TestData(
        tenant_ignore=IgnoreReason.TENANT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateKeyValueTags'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateOrganization'): TestData(
        tenant_perm=MANAGE_ORGANIZATIONS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateOrganizationGroup'): TestData(
        tenant_perm=MANAGE_ORGANIZATIONS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateRedshiftDataset'): TestData(
        tenant_perm=MANAGE_REDSHIFT_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateRedshiftDatasetTable'): TestData(
        tenant_perm=MANAGE_REDSHIFT_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateSSMParameter'): TestData(
        tenant_ignore=IgnoreReason.TENANT, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateShareExpirationPeriod'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateShareExtensionReason'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateShareItemFilters'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateShareRejectReason'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateShareRequestReason'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateStack'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateTerm'): TestData(
        tenant_perm=MANAGE_GLOSSARIES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'updateWorksheet'): TestData(
        tenant_perm=MANAGE_WORKSHEETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'verifyDatasetShareObjects'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Mutation', 'verifyItemsShareObject'): TestData(
        tenant_perm=MANAGE_SHARES, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('OmicsRun', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('OmicsRun', 'organization'): TestData(
        resource_perm=GET_ORGANIZATION, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('OmicsRun', 'status'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('OmicsRun', 'workflow'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Organization', 'environments'): TestData(
        resource_perm=GET_ORGANIZATION, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Organization', 'stats'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Organization', 'userRoleInOrganization'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Permission', 'type'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'countDeletedNotifications'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'countReadNotifications'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'countUnreadNotifications'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'countUpVotes'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'generateEnvironmentAccessToken'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getAttachedMetadataForm'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getAuthorSession'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getCDKExecPolicyPresignedUrl'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getConsumptionRolePolicies'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDashboard'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDataPipeline'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDataPipelineCredsLinux'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDataset'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDatasetAssumeRoleUrl'): TestData(
        tenant_perm=MANAGE_DATASETS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDatasetPresignedUrl'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDatasetSharedAssumeRoleUrl'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDatasetStorageLocation'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDatasetTable'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getDatasetTableProfilingRun'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getEntityMetadataFormPermissions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getEnvironment'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getEnvironmentAssumeRoleUrl'): TestData(
        tenant_perm=MANAGE_ENVIRONMENTS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getEnvironmentMLStudioDomain'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getFeed'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getGlossary'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getGroup'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getGroupsForUser'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getMaintenanceWindowStatus'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getMetadataForm'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getMonitoringDashboardId'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getMonitoringVPCConnectionId'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getOmicsWorkflow'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getOrganization'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getPivotRoleExternalId'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getPivotRoleName'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getPivotRolePresignedUrl'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getPlatformAuthorSession'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getPlatformReaderSession'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getReaderSession'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getRedshiftDataset'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getRedshiftDatasetTable'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getRedshiftDatasetTableColumns'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getS3ConsumptionData'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getSagemakerNotebook'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getSagemakerNotebookPresignedUrl'): TestData(
        tenant_perm=MANAGE_NOTEBOOKS, resource_perm=GET_NOTEBOOK
    ),
    field_id('Query', 'getSagemakerStudioUser'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getSagemakerStudioUserPresignedUrl'): TestData(
        tenant_perm=MANAGE_SGMSTUDIO_USERS, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getShareItemDataFilters'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getShareLogs'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getShareObject'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getShareRequestsFromMe'): TestData(
        tenant_ignore=IgnoreReason.USERLIMITED, resource_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getShareRequestsToMe'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getSharedDatasetTables'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getStack'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getStackLogs'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getTrustAccount'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getVote'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'getWorksheet'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listAllConsumptionRoles'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listAllEnvironmentConsumptionRoles'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listAllEnvironmentGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listAllGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listAttachedMetadataForms'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listConnectionGroupNoPermissions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listConnectionGroupPermissions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDashboardShares'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDataPipelines'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDatasetTableColumns'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDatasetTableProfilingRuns'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDatasetTables'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDatasets'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listDatasetsCreatedInEnvironment'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEntityMetadataForms'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironmentConsumptionRoles'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironmentGroupInvitationPermissions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironmentGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironmentInvitedGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironmentNetworks'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironmentRedshiftConnections'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listEnvironments'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listGlossaries'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listInviteOrganizationPermissionsWithDescriptions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listKeyValueTags'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listMetadataFormVersions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listNotifications'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listOmicsRuns'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listOmicsWorkflows'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listOrganizationGroupPermissions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listOrganizationGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listOrganizations'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listOwnedDatasets'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listRedshiftConnectionSchemas'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listRedshiftDatasetTables'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listRedshiftSchemaDatasetTables'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listRedshiftSchemaTables'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listS3DatasetsOwnedByEnvGroup'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listS3DatasetsSharedWithEnvGroup'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listSagemakerNotebooks'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listSagemakerStudioUsers'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listSharedDatasetTableColumns'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listTableDataFilters'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listTableDataFiltersByAttached'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listTenantGroups'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listTenantPermissions'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listUserMetadataForms'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listUsersForGroup'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listValidEnvironments'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'listWorksheets'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'previewTable'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'queryEnums'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'runAthenaSqlQuery'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'searchDashboards'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'searchEnvironmentDataItems'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Query', 'searchGlossary'): TestData(
        resource_ignore=IgnoreReason.NOTREQUIRED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'connection'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'owners'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'stewards'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'terms'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'upvotes'): TestData(
        resource_ignore=IgnoreReason.APPSUPPORT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDataset', 'userRoleForDataset'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDatasetTable', 'dataset'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('RedshiftDatasetTable', 'terms'): TestData(
        resource_ignore=IgnoreReason.PUBLIC, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerNotebook', 'NotebookInstanceStatus'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerNotebook', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerNotebook', 'organization'): TestData(
        resource_perm=GET_ORGANIZATION, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerNotebook', 'stack'): TestData(
        resource_perm=GET_NOTEBOOK, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerNotebook', 'userRoleForNotebook'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioDomain', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioUser', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioUser', 'organization'): TestData(
        resource_perm=GET_ORGANIZATION, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioUser', 'sagemakerStudioUserApps'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioUser', 'sagemakerStudioUserStatus'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioUser', 'stack'): TestData(
        resource_perm=GET_SGMSTUDIO_USER, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SagemakerStudioUser', 'userRoleForSagemakerStudioUser'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'canViewLogs'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'dataset'): TestData(
        resource_ignore=IgnoreReason.SIMPLIFIED, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'environment'): TestData(
        resource_perm=GET_ENVIRONMENT, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'existingSharedItems'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'group'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'items'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'principal'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'statistics'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('ShareObject', 'userRoleForShareObject'): TestData(
        resource_ignore=IgnoreReason.USERROLEINRESOURCE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('SharedDatabaseTableItem', 'sharedGlueDatabaseName'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'EcsTaskId'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'canViewLogs'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'error'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'events'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'link'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'outputs'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Stack', 'resources'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Term', 'associations'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Term', 'children'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Term', 'glossary'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Term', 'stats'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
    field_id('Worksheet', 'userRoleForWorksheet'): TestData(
        resource_ignore=IgnoreReason.INTRAMODULE, tenant_ignore=IgnoreReason.NOTREQUIRED
    ),
}

ALL_RESOLVERS = {(_type, field) for _type in bootstrap().types for field in _type.fields if field.resolver}


def test_all_resolvers_have_test_data():
    """
    ensure that all EXPECTED_RESOURCES_PERMS have a corresponding query (to avoid stale entries) and vice versa
    """
    assert_that([field_id(res[0].name, res[1].name) for res in ALL_RESOLVERS]).described_as(
        'stale or missing EXPECTED_RESOURCE_PERMS detected'
    ).contains_only(*EXPECTED_RESOLVERS.keys())


ALL_PARAMS = [pytest.param(_type, field, id=field_id(_type.name, field.name)) for _type, field in ALL_RESOLVERS]


@pytest.fixture(scope='function')
def mock_input_validation(mocker):
    mocker.patch('dataall.modules.mlstudio.api.resolvers.RequestValidator', MagicMock())
    mocker.patch(
        'dataall.modules.mlstudio.services.mlstudio_service.SagemakerStudioCreationRequest.from_dict', MagicMock()
    )
    mocker.patch('dataall.modules.notebooks.api.resolvers.RequestValidator', MagicMock())
    mocker.patch('dataall.modules.notebooks.services.notebook_service.NotebookCreationRequest.from_dict', MagicMock())
    mocker.patch('dataall.modules.s3_datasets.api.profiling.resolvers._validate_uri', MagicMock())
    mocker.patch('dataall.modules.s3_datasets.api.storage_location.resolvers._validate_input', MagicMock())
    mocker.patch('dataall.modules.s3_datasets.api.dataset.resolvers.RequestValidator', MagicMock())
    mocker.patch(
        'dataall.core.stacks.db.target_type_repositories.TargetType.get_resource_tenant_permission_name',
        return_value='MANAGE_ENVIRONMENTS',
    )
    mocker.patch('dataall.modules.shares_base.api.resolvers.RequestValidator', MagicMock())


@pytest.mark.parametrize('_type,field', ALL_PARAMS)
@patch('dataall.base.context._request_storage')
@patch('dataall.core.permissions.services.resource_policy_service.ResourcePolicyService.check_user_resource_permission')
@patch('dataall.core.permissions.services.group_policy_service.GroupPolicyService.check_group_environment_permission')
@patch('dataall.core.permissions.services.tenant_policy_service.TenantPolicyService.check_user_tenant_permission')
def test_unauthorized_tenant_permissions(
    mock_tenant_check,
    mock_check_group,
    mock_check_resource,
    mock_storage,
    _type,
    field,
    request,
    mock_input_validation,
):
    fid = request.node.callspec.id
    tdata = EXPECTED_RESOLVERS[fid]
    msg = f'{fid} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    expected_perm = tdata.tenant_perm
    if not expected_perm:
        pytest.skip(msg + f' Reason: {tdata.tenant_ignore.value}')
    logging.info(msg)

    assert_that(field.resolver).is_not_none()
    username = 'ausername'
    groups = ['agroup']
    mock_storage.context = RequestContext(MagicMock(), username, groups, 'auserid')
    mock_tenant_check.side_effect = TenantUnauthorized(username, 'test_action', 'test_tenant')
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    assert_that(field.resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation')
    mock_tenant_check.assert_called_once_with(
        session=ANY, username=username, groups=groups, tenant_name=ANY, permission_name=expected_perm
    )


@patch('dataall.base.aws.sts.SessionHelper.remote_session')
@patch('dataall.core.stacks.db.target_type_repositories.TargetType.get_resource_read_permission_name')
@patch('dataall.core.permissions.services.resource_policy_service.ResourcePolicyService.check_user_resource_permission')
@patch('dataall.base.context._request_storage')
@pytest.mark.parametrize('_type,field', ALL_PARAMS)
def test_unauthorized_resource_permissions(
    mock_storage,
    mock_check,
    mock_perm_name,
    mock_session,
    _type,
    field,
    request,
):
    fid = request.node.callspec.id
    tdata = EXPECTED_RESOLVERS[fid]
    msg = f'{fid} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    expected_perm = tdata.resource_perm
    if not expected_perm:
        pytest.skip(msg + f' Reason: {tdata.resource_ignore.value}')
    logging.info(msg)

    assert_that(field.resolver).is_not_none()
    username = 'ausername'
    groups = ['agroup']
    mock_storage.context = RequestContext(MagicMock(), username, groups, 'auserid')
    mock_storage.context.db_engine.scoped_session().__enter__().query().filter().all.return_value = [MagicMock()]
    mock_check.side_effect = ResourceUnauthorized(groups, 'test_action', 'test_uri')
    mock_perm_name.return_value = expected_perm
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    with suppress(ResourceUnauthorized):
        field.resolver(**iargs)
    mock_check.assert_called_once_with(
        session=ANY,
        resource_uri=ANY,
        username=username,
        groups=groups,
        permission_name=expected_perm,
    )
