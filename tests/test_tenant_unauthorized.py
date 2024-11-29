import inspect
import logging
from contextlib import suppress
from enum import Enum
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
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.catalog.services.glossaries_permissions import MANAGE_GLOSSARIES
from dataall.modules.dashboards.services.dashboard_permissions import MANAGE_DASHBOARDS
from dataall.modules.datapipelines.services.datapipelines_permissions import GET_PIPELINE, MANAGE_PIPELINES
from dataall.modules.metadata_forms.services.metadata_form_permissions import MANAGE_METADATA_FORMS
from dataall.modules.mlstudio.services.mlstudio_permissions import GET_SGMSTUDIO_USER, MANAGE_SGMSTUDIO_USERS
from dataall.modules.notebooks.services.notebook_permissions import GET_NOTEBOOK, MANAGE_NOTEBOOKS
from dataall.modules.omics.services.omics_permissions import MANAGE_OMICS_RUNS
from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import MANAGE_REDSHIFT_DATASETS
from dataall.modules.s3_datasets.services.dataset_permissions import GET_DATASET, GET_DATASET_TABLE, MANAGE_DATASETS
from dataall.modules.shares_base.services.share_permissions import MANAGE_SHARES
from dataall.modules.worksheets.services.worksheet_permissions import MANAGE_WORKSHEETS


def resolver_id(type_name, field_name):
    return f'{type_name}_{field_name}'


SKIP_MARK = '@SKIP@'


class IgnoreReason(Enum):
    ADMIN = f'{SKIP_MARK} admin action. No need for tenant permission check'
    SUPPORT = f'{SKIP_MARK} permissions do not apply to support notifications'
    FEED = f'{SKIP_MARK} permissions do not apply to support feed messages'
    VOTES = f'{SKIP_MARK} permissions do not apply to support votes'
    BACKPORT = f'{SKIP_MARK} outside of this PR to be able to backport to v2.6.2'
    INTRAMODULE = f'{SKIP_MARK} returns intra-module data'
    PERMCHECK = f'{SKIP_MARK} checks user permissions for a particular feature'
    CATALOG = f'{SKIP_MARK} catalog resources are public by design'
    SIMPLIFIED = f'{SKIP_MARK} simplified response'
    NOTIMPLEMENTED = f'{SKIP_MARK} not implemented'


def field_id(type_name: str, field_name: str) -> str:
    return f'{type_name}_{field_name}'


ALL_RESOLVERS = {(_type, field) for _type in bootstrap().types for field in _type.fields if field.resolver}

TOP_LEVEL_QUERIES = {
    field_id('Mutation', 'DisableDataSubscriptions'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'addConsumptionRoleToEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'addRedshiftDatasetTables'): MANAGE_REDSHIFT_DATASETS,
    field_id('Mutation', 'addSharedItem'): MANAGE_SHARES,
    field_id('Mutation', 'approveDashboardShare'): MANAGE_DASHBOARDS,
    field_id('Mutation', 'approveShareExtension'): MANAGE_SHARES,
    field_id('Mutation', 'approveShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'approveTermAssociation'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'archiveOrganization'): MANAGE_ORGANIZATIONS,
    field_id('Mutation', 'batchMetadataFormFieldUpdates'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'cancelShareExtension'): MANAGE_SHARES,
    field_id('Mutation', 'createCategory'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'createDataPipeline'): MANAGE_PIPELINES,
    field_id('Mutation', 'createDataPipelineEnvironment'): MANAGE_PIPELINES,
    field_id('Mutation', 'createDataset'): MANAGE_DATASETS,
    field_id('Mutation', 'createDatasetStorageLocation'): MANAGE_DATASETS,
    field_id('Mutation', 'createEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'createGlossary'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'createMetadataForm'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'createMetadataFormFields'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'createMetadataFormVersion'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'createNetwork'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'createOmicsRun'): MANAGE_OMICS_RUNS,
    field_id('Mutation', 'createOrganization'): MANAGE_ORGANIZATIONS,
    field_id('Mutation', 'createSagemakerNotebook'): MANAGE_NOTEBOOKS,
    field_id('Mutation', 'createSagemakerStudioUser'): MANAGE_SGMSTUDIO_USERS,
    field_id('Mutation', 'createShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'createTableDataFilter'): MANAGE_DATASETS,
    field_id('Mutation', 'createTerm'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'createWorksheet'): MANAGE_WORKSHEETS,
    field_id('Mutation', 'deleteCategory'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'deleteDashboard'): MANAGE_DASHBOARDS,
    field_id('Mutation', 'deleteDataPipeline'): MANAGE_PIPELINES,
    field_id('Mutation', 'deleteDataPipelineEnvironment'): MANAGE_PIPELINES,
    field_id('Mutation', 'deleteDataset'): MANAGE_DATASETS,
    field_id('Mutation', 'deleteDatasetStorageLocation'): MANAGE_DATASETS,
    field_id('Mutation', 'deleteDatasetTable'): MANAGE_DATASETS,
    field_id('Mutation', 'deleteEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'deleteGlossary'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'deleteMetadataForm'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'deleteMetadataFormField'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'deleteMetadataFormVersion'): MANAGE_METADATA_FORMS,
    field_id('Mutation', 'deleteNetwork'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'deleteOmicsRun'): MANAGE_OMICS_RUNS,
    field_id('Mutation', 'deleteRedshiftDataset'): MANAGE_REDSHIFT_DATASETS,
    field_id('Mutation', 'deleteRedshiftDatasetTable'): MANAGE_REDSHIFT_DATASETS,
    field_id('Mutation', 'deleteSagemakerNotebook'): MANAGE_NOTEBOOKS,
    field_id('Mutation', 'deleteSagemakerStudioUser'): MANAGE_SGMSTUDIO_USERS,
    field_id('Mutation', 'deleteShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'deleteTableDataFilter'): MANAGE_DATASETS,
    field_id('Mutation', 'deleteTerm'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'deleteWorksheet'): MANAGE_WORKSHEETS,
    field_id('Mutation', 'dismissTermAssociation'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'enableDataSubscriptions'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'generateDatasetAccessToken'): MANAGE_DATASETS,
    field_id('Mutation', 'importDashboard'): MANAGE_DASHBOARDS,
    field_id('Mutation', 'importDataset'): MANAGE_DATASETS,
    field_id('Mutation', 'importRedshiftDataset'): MANAGE_REDSHIFT_DATASETS,
    field_id('Mutation', 'inviteGroupOnEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'inviteGroupToOrganization'): MANAGE_ORGANIZATIONS,
    field_id('Mutation', 'reApplyItemsShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'reApplyShareObjectItemsOnDataset'): MANAGE_DATASETS,
    field_id('Mutation', 'rejectDashboardShare'): MANAGE_DASHBOARDS,
    field_id('Mutation', 'rejectShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'removeConsumptionRoleFromEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'removeGroupFromEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'removeGroupFromOrganization'): MANAGE_ORGANIZATIONS,
    field_id('Mutation', 'removeShareItemFilter'): MANAGE_SHARES,
    field_id('Mutation', 'removeSharedItem'): MANAGE_SHARES,
    field_id('Mutation', 'requestDashboardShare'): MANAGE_DASHBOARDS,
    field_id('Mutation', 'revokeItemsShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'startDatasetProfilingRun'): MANAGE_DATASETS,
    field_id('Mutation', 'startGlueCrawler'): MANAGE_DATASETS,
    field_id('Mutation', 'startSagemakerNotebook'): MANAGE_NOTEBOOKS,
    field_id('Mutation', 'stopSagemakerNotebook'): MANAGE_NOTEBOOKS,
    field_id('Mutation', 'submitShareExtension'): MANAGE_SHARES,
    field_id('Mutation', 'submitShareObject'): MANAGE_SHARES,
    field_id('Mutation', 'syncDatasetTableColumns'): MANAGE_DATASETS,
    field_id('Mutation', 'syncTables'): MANAGE_DATASETS,
    field_id('Mutation', 'updateCategory'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'updateConsumptionRole'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'updateDashboard'): MANAGE_DASHBOARDS,
    field_id('Mutation', 'updateDataPipeline'): MANAGE_PIPELINES,
    field_id('Mutation', 'updateDataPipelineEnvironment'): MANAGE_PIPELINES,
    field_id('Mutation', 'updateDataset'): MANAGE_DATASETS,
    field_id('Mutation', 'updateDatasetStorageLocation'): MANAGE_DATASETS,
    field_id('Mutation', 'updateDatasetTable'): MANAGE_DATASETS,
    field_id('Mutation', 'updateDatasetTableColumn'): MANAGE_DATASETS,
    field_id('Mutation', 'updateEnvironment'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'updateGlossary'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'updateGroupEnvironmentPermissions'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'updateKeyValueTags'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'updateOrganization'): MANAGE_ORGANIZATIONS,
    field_id('Mutation', 'updateOrganizationGroup'): MANAGE_ORGANIZATIONS,
    field_id('Mutation', 'updateRedshiftDataset'): MANAGE_REDSHIFT_DATASETS,
    field_id('Mutation', 'updateRedshiftDatasetTable'): MANAGE_REDSHIFT_DATASETS,
    field_id('Mutation', 'updateShareExpirationPeriod'): MANAGE_SHARES,
    field_id('Mutation', 'updateShareExtensionReason'): MANAGE_SHARES,
    field_id('Mutation', 'updateShareItemFilters'): MANAGE_SHARES,
    field_id('Mutation', 'updateShareRejectReason'): MANAGE_SHARES,
    field_id('Mutation', 'updateShareRequestReason'): MANAGE_SHARES,
    field_id('Mutation', 'updateStack'): MANAGE_ENVIRONMENTS,
    field_id('Mutation', 'updateTerm'): MANAGE_GLOSSARIES,
    field_id('Mutation', 'updateWorksheet'): MANAGE_WORKSHEETS,
    field_id('Mutation', 'verifyDatasetShareObjects'): MANAGE_DATASETS,
    field_id('Mutation', 'verifyItemsShareObject'): MANAGE_SHARES,
    field_id('Query', 'countDeletedNotifications'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'countReadNotifications'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'countUnreadNotifications'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'countUpVotes'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'generateEnvironmentAccessToken'): MANAGE_ENVIRONMENTS,
    field_id('Query', 'getAttachedMetadataForm'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getAuthorSession'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getCDKExecPolicyPresignedUrl'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getConsumptionRolePolicies'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDashboard'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDataPipeline'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDataPipelineCredsLinux'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDataset'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDatasetAssumeRoleUrl'): MANAGE_DATASETS,
    field_id('Query', 'getDatasetPresignedUrl'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDatasetSharedAssumeRoleUrl'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDatasetStorageLocation'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDatasetTable'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getDatasetTableProfilingRun'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getEntityMetadataFormPermissions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getEnvironment'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getEnvironmentAssumeRoleUrl'): MANAGE_ENVIRONMENTS,
    field_id('Query', 'getEnvironmentMLStudioDomain'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getFeed'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getGlossary'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getGroup'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getGroupsForUser'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getMaintenanceWindowStatus'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getMetadataForm'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getMonitoringDashboardId'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getMonitoringVPCConnectionId'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getOmicsWorkflow'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getOrganization'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getPivotRoleExternalId'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getPivotRoleName'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getPivotRolePresignedUrl'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getPlatformAuthorSession'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getPlatformReaderSession'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getReaderSession'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getRedshiftDataset'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getRedshiftDatasetTable'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getRedshiftDatasetTableColumns'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getS3ConsumptionData'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getSagemakerNotebook'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getSagemakerNotebookPresignedUrl'): MANAGE_NOTEBOOKS,
    field_id('Query', 'getSagemakerStudioUser'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getSagemakerStudioUserPresignedUrl'): MANAGE_SGMSTUDIO_USERS,
    field_id('Query', 'getShareItemDataFilters'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getShareLogs'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getShareObject'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getShareRequestsFromMe'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getShareRequestsToMe'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getSharedDatasetTables'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getStack'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getStackLogs'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getTrustAccount'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getVote'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'getWorksheet'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listAllConsumptionRoles'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listAllEnvironmentConsumptionRoles'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listAllEnvironmentGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listAllGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listAttachedMetadataForms'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listConnectionGroupNoPermissions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listConnectionGroupPermissions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDashboardShares'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDataPipelines'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDatasetTableColumns'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDatasetTableProfilingRuns'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDatasetTables'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDatasets'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listDatasetsCreatedInEnvironment'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEntityMetadataForms'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironmentConsumptionRoles'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironmentGroupInvitationPermissions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironmentGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironmentInvitedGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironmentNetworks'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironmentRedshiftConnections'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listEnvironments'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listGlossaries'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listInviteOrganizationPermissionsWithDescriptions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listKeyValueTags'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listMetadataFormVersions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listNotifications'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listOmicsRuns'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listOmicsWorkflows'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listOrganizationGroupPermissions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listOrganizationGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listOrganizations'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listOwnedDatasets'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listRedshiftConnectionSchemas'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listRedshiftDatasetTables'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listRedshiftSchemaDatasetTables'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listRedshiftSchemaTables'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listS3DatasetsOwnedByEnvGroup'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listS3DatasetsSharedWithEnvGroup'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listSagemakerNotebooks'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listSagemakerStudioUsers'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listSharedDatasetTableColumns'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listTableDataFilters'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listTableDataFiltersByAttached'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listTenantGroups'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listTenantPermissions'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listUserMetadataForms'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listUsersForGroup'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listValidEnvironments'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'listWorksheets'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'previewTable'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'queryEnums'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'runAthenaSqlQuery'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'searchDashboards'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'searchEnvironmentDataItems'): IgnoreReason.NOTIMPLEMENTED.value,
    field_id('Query', 'searchGlossary'): IgnoreReason.NOTIMPLEMENTED.value,
    # Admin actions
    field_id('Mutation', 'updateGroupTenantPermissions'): IgnoreReason.ADMIN.value,
    field_id('Mutation', 'updateSSMParameter'): IgnoreReason.ADMIN.value,
    field_id('Mutation', 'createQuicksightDataSourceSet'): IgnoreReason.ADMIN.value,
    field_id('Mutation', 'startMaintenanceWindow'): IgnoreReason.ADMIN.value,
    field_id('Mutation', 'stopMaintenanceWindow'): IgnoreReason.ADMIN.value,
    field_id('Mutation', 'startReindexCatalog'): IgnoreReason.ADMIN.value,
    # Support-related actions
    field_id('Mutation', 'markNotificationAsRead'): IgnoreReason.SUPPORT.value,
    field_id('Mutation', 'deleteNotification'): IgnoreReason.SUPPORT.value,
    field_id('Mutation', 'postFeedMessage'): IgnoreReason.FEED.value,
    field_id('Mutation', 'upVote'): IgnoreReason.VOTES.value,
    # Backport-related actions
    field_id('Mutation', 'createAttachedMetadataForm'): IgnoreReason.BACKPORT.value,
    field_id('Mutation', 'deleteAttachedMetadataForm'): IgnoreReason.BACKPORT.value,
    field_id('Mutation', 'createRedshiftConnection'): IgnoreReason.BACKPORT.value,
    field_id('Mutation', 'deleteRedshiftConnection'): IgnoreReason.BACKPORT.value,
    field_id('Mutation', 'addConnectionGroupPermission'): IgnoreReason.BACKPORT.value,
    field_id('Mutation', 'deleteConnectionGroupPermission'): IgnoreReason.BACKPORT.value,
}


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


@pytest.mark.parametrize(
    '_type,field',
    [
        pytest.param(_type, field, id=field_id(_type.name, field.name))
        for _type, field in ALL_RESOLVERS
        if _type.name in ['Query', 'Mutation']
    ],
)
@patch('dataall.core.permissions.services.tenant_policy_service.TenantPolicyService.check_user_tenant_permission', wraps=TenantPolicyService.check_user_tenant_permission)
@patch('dataall.base.context._request_storage')
def test_unauthorized_tenant_permissions(
    mock_local,
    spy_check,
    _type,
    field,
    request,
    mock_input_validation,
    db,
    userNoTenantPermissions,
    groupNoTenantPermissions,
):
    fid = request.node.callspec.id
    expected_perm = TOP_LEVEL_QUERIES.get(fid, 'NON_EXISTENT_PERM')
    msg = f'{fid} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    if SKIP_MARK in expected_perm:
        pytest.skip(msg + f' Reason: {expected_perm}')
    logging.info(msg)

    assert_that(field.resolver).is_not_none()
    groups = [groupNoTenantPermissions.groupUri]
    username = userNoTenantPermissions.username
    mock_local.context = RequestContext(
        db, username, groups, userNoTenantPermissions
    )
    # Mocking arguments
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    # Assert Unauthorized exception is raised
    assert_that(field.resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation')
    spy_check.assert_called_once_with(session=ANY, username=username, groups=groups, tenant_name=ANY, permission_name=expected_perm)


EXPECTED_RESOURCE_PERMS = {
    field_id('AttachedMetadataFormField', 'field'): IgnoreReason.INTRAMODULE.value,
    field_id('AttachedMetadataFormField', 'hasTenantPermissions'): IgnoreReason.PERMCHECK.value,
    field_id('AttachedMetadataForm', 'entityName'): IgnoreReason.INTRAMODULE.value,
    field_id('AttachedMetadataForm', 'fields'): IgnoreReason.INTRAMODULE.value,
    field_id('AttachedMetadataForm', 'metadataForm'): IgnoreReason.INTRAMODULE.value,
    field_id('Category', 'associations'): IgnoreReason.INTRAMODULE.value,
    field_id('Category', 'categories'): IgnoreReason.INTRAMODULE.value,
    field_id('Category', 'children'): IgnoreReason.INTRAMODULE.value,
    field_id('Category', 'stats'): IgnoreReason.INTRAMODULE.value,
    field_id('Category', 'terms'): IgnoreReason.INTRAMODULE.value,
    field_id('ConsumptionRole', 'managedPolicies'): GET_ENVIRONMENT,
    field_id('Dashboard', 'environment'): GET_ENVIRONMENT,
    field_id('Dashboard', 'terms'): IgnoreReason.CATALOG.value,
    field_id('Dashboard', 'upvotes'): IgnoreReason.VOTES.value,
    field_id('Dashboard', 'userRoleForDashboard'): IgnoreReason.INTRAMODULE.value,
    field_id('DataPipeline', 'cloneUrlHttp'): IgnoreReason.INTRAMODULE.value,
    field_id('DataPipeline', 'developmentEnvironments'): IgnoreReason.INTRAMODULE.value,
    field_id('DataPipeline', 'environment'): GET_ENVIRONMENT,
    field_id('DataPipeline', 'organization'): GET_ORGANIZATION,
    field_id('DataPipeline', 'stack'): GET_PIPELINE,
    field_id('DataPipeline', 'userRoleForPipeline'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetBase', 'environment'): GET_ENVIRONMENT,
    field_id('DatasetBase', 'owners'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetBase', 'stack'): GET_DATASET,
    field_id('DatasetBase', 'stewards'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetBase', 'userRoleForDataset'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetProfilingRun', 'dataset'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetProfilingRun', 'results'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetProfilingRun', 'status'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetStorageLocation', 'dataset'): GET_DATASET,
    field_id('DatasetStorageLocation', 'terms'): IgnoreReason.CATALOG.value,
    field_id('DatasetTableColumn', 'terms'): IgnoreReason.CATALOG.value,
    field_id('DatasetTable', 'GlueTableProperties'): GET_DATASET_TABLE,
    field_id('DatasetTable', 'columns'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetTable', 'dataset'): IgnoreReason.INTRAMODULE.value,
    field_id('DatasetTable', 'terms'): IgnoreReason.CATALOG.value,
    field_id('Dataset', 'environment'): GET_ENVIRONMENT,
    field_id('Dataset', 'locations'): IgnoreReason.INTRAMODULE.value,
    field_id('Dataset', 'owners'): IgnoreReason.INTRAMODULE.value,
    field_id('Dataset', 'stack'): GET_DATASET,
    field_id('Dataset', 'statistics'): IgnoreReason.INTRAMODULE.value,
    field_id('Dataset', 'stewards'): IgnoreReason.INTRAMODULE.value,
    field_id('Dataset', 'tables'): IgnoreReason.INTRAMODULE.value,
    field_id('Dataset', 'terms'): IgnoreReason.CATALOG.value,
    field_id('Dataset', 'userRoleForDataset'): IgnoreReason.INTRAMODULE.value,
    field_id('EnvironmentSimplified', 'networks'): GET_NETWORK,
    field_id('EnvironmentSimplified', 'organization'): IgnoreReason.SIMPLIFIED.value,
    field_id('Environment', 'networks'): GET_NETWORK,
    field_id('Environment', 'organization'): IgnoreReason.SIMPLIFIED.value,
    field_id('Environment', 'parameters'): IgnoreReason.INTRAMODULE.value,
    field_id('Environment', 'stack'): GET_ENVIRONMENT,
    field_id('Environment', 'userRoleInEnvironment'): IgnoreReason.INTRAMODULE.value,
    field_id('Feed', 'messages'): IgnoreReason.FEED.value,
    field_id('GlossaryTermLink', 'target'): IgnoreReason.CATALOG.value,
    field_id('GlossaryTermLink', 'term'): IgnoreReason.CATALOG.value,
    field_id('Glossary', 'associations'): IgnoreReason.CATALOG.value,
    field_id('Glossary', 'categories'): IgnoreReason.CATALOG.value,
    field_id('Glossary', 'children'): IgnoreReason.CATALOG.value,
    field_id('Glossary', 'stats'): IgnoreReason.CATALOG.value,
    field_id('Glossary', 'tree'): IgnoreReason.CATALOG.value,
    field_id('Glossary', 'userRoleForGlossary'): IgnoreReason.CATALOG.value,
    field_id('Group', 'environmentPermissions'): IgnoreReason.PERMCHECK.value,
    field_id('Group', 'tenantPermissions'): IgnoreReason.PERMCHECK.value,
    field_id('MetadataFormField', 'glossaryNodeName'): IgnoreReason.CATALOG.value,
    field_id('MetadataFormSearchResult', 'hasTenantPermissions'): IgnoreReason.PERMCHECK.value,
    field_id('MetadataForm', 'fields'): IgnoreReason.INTRAMODULE.value,
    field_id('MetadataForm', 'homeEntityName'): IgnoreReason.INTRAMODULE.value,
    field_id('MetadataForm', 'userRole'): IgnoreReason.INTRAMODULE.value,
    field_id('OmicsRun', 'environment'): GET_ENVIRONMENT,
    field_id('OmicsRun', 'organization'): GET_ORGANIZATION,
    field_id('OmicsRun', 'status'): IgnoreReason.INTRAMODULE.value,
    field_id('OmicsRun', 'workflow'): IgnoreReason.INTRAMODULE.value,
    field_id('Organization', 'environments'): GET_ORGANIZATION,
    field_id('Organization', 'stats'): IgnoreReason.INTRAMODULE.value,
    field_id('Organization', 'userRoleInOrganization'): IgnoreReason.INTRAMODULE.value,
    field_id('Permission', 'type'): IgnoreReason.INTRAMODULE.value,
    field_id('RedshiftDataset', 'connection'): IgnoreReason.INTRAMODULE.value,
    field_id('RedshiftDataset', 'environment'): GET_ENVIRONMENT,
    field_id('RedshiftDataset', 'owners'): IgnoreReason.INTRAMODULE.value,
    field_id('RedshiftDataset', 'stewards'): IgnoreReason.INTRAMODULE.value,
    field_id('RedshiftDataset', 'terms'): IgnoreReason.CATALOG.value,
    field_id('RedshiftDataset', 'upvotes'): IgnoreReason.VOTES.value,
    field_id('RedshiftDataset', 'userRoleForDataset'): IgnoreReason.INTRAMODULE.value,
    field_id('RedshiftDatasetTable', 'dataset'): IgnoreReason.INTRAMODULE.value,
    field_id('RedshiftDatasetTable', 'terms'): IgnoreReason.CATALOG.value,
    field_id('SagemakerNotebook', 'environment'): GET_ENVIRONMENT,
    field_id('SagemakerNotebook', 'NotebookInstanceStatus'): IgnoreReason.INTRAMODULE.value,
    field_id('SagemakerNotebook', 'organization'): GET_ORGANIZATION,
    field_id('SagemakerNotebook', 'stack'): GET_NOTEBOOK,
    field_id('SagemakerNotebook', 'userRoleForNotebook'): IgnoreReason.INTRAMODULE.value,
    field_id('SagemakerStudioDomain', 'environment'): GET_ENVIRONMENT,
    field_id('SagemakerStudioUser', 'environment'): GET_ENVIRONMENT,
    field_id('SagemakerStudioUser', 'organization'): GET_ORGANIZATION,
    field_id('SagemakerStudioUser', 'sagemakerStudioUserApps'): IgnoreReason.INTRAMODULE.value,
    field_id('SagemakerStudioUser', 'sagemakerStudioUserStatus'): IgnoreReason.INTRAMODULE.value,
    field_id('SagemakerStudioUser', 'stack'): GET_SGMSTUDIO_USER,
    field_id('SagemakerStudioUser', 'userRoleForSagemakerStudioUser'): IgnoreReason.INTRAMODULE.value,
    field_id('SharedDatabaseTableItem', 'sharedGlueDatabaseName'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'canViewLogs'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'dataset'): IgnoreReason.SIMPLIFIED.value,
    field_id('ShareObject', 'environment'): GET_ENVIRONMENT,
    field_id('ShareObject', 'existingSharedItems'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'group'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'items'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'principal'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'statistics'): IgnoreReason.INTRAMODULE.value,
    field_id('ShareObject', 'userRoleForShareObject'): IgnoreReason.PERMCHECK.value,
    field_id('Stack', 'canViewLogs'): IgnoreReason.INTRAMODULE.value,
    field_id('Stack', 'EcsTaskId'): IgnoreReason.INTRAMODULE.value,
    field_id('Stack', 'error'): IgnoreReason.INTRAMODULE.value,
    field_id('Stack', 'events'): IgnoreReason.INTRAMODULE.value,
    field_id('Stack', 'link'): IgnoreReason.INTRAMODULE.value,
    field_id('Stack', 'outputs'): IgnoreReason.INTRAMODULE.value,
    field_id('Stack', 'resources'): IgnoreReason.INTRAMODULE.value,
    field_id('Term', 'associations'): IgnoreReason.INTRAMODULE.value,
    field_id('Term', 'children'): IgnoreReason.INTRAMODULE.value,
    field_id('Term', 'glossary'): IgnoreReason.INTRAMODULE.value,
    field_id('Term', 'stats'): IgnoreReason.INTRAMODULE.value,
    field_id('Worksheet', 'userRoleForWorksheet'): IgnoreReason.INTRAMODULE.value,
}

PARAMS = [
    pytest.param(field, id=field_id(_type.name, field.name))
    for _type, field in ALL_RESOLVERS
    if _type.name not in ['Query', 'Mutation']  # filter out top-level queries (don't print skip)
]
# ensure that all EXPECTED_RESOURCES_PERMS have a corresponding query (to avoid stale entries) and vice versa
assert_that(PARAMS).described_as('stale or missing EXPECTED_RESOURCE_PERMS detected').extracting(2).contains_only(
    *EXPECTED_RESOURCE_PERMS.keys()
)


@patch('dataall.base.aws.sts.SessionHelper.remote_session')
@patch('dataall.core.permissions.services.resource_policy_service.ResourcePolicyService.check_user_resource_permission')
@patch('dataall.base.context._request_storage')
@pytest.mark.parametrize('field', PARAMS)
def test_unauthorized_resource_permissions(
    mock_local,
    mock_check,
    mock_session,
    field,
    request,
):
    fid = request.node.callspec.id
    expected_perm = EXPECTED_RESOURCE_PERMS.get(fid, 'NON_EXISTENT_PERM')
    msg = f'{fid} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    if SKIP_MARK in expected_perm:
        pytest.skip(msg + f' Reason: {expected_perm}')
    logging.info(msg)

    assert_that(field.resolver).is_not_none()
    username = 'ausername'
    groups = ['agroup']
    mock_local.context = RequestContext(MagicMock(), username, groups, 'auserid')
    mock_local.context.db_engine.scoped_session().__enter__().query().filter().all.return_value = [MagicMock()]
    mock_check.side_effect = ResourceUnauthorized(groups, 'test_action', 'test_uri')
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
