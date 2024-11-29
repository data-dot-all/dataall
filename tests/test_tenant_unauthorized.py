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


@dataclass
class TestData:
    resource_ignore: IgnoreReason = IgnoreReason.NOTIMPLEMENTED
    resource_perm: str = None
    tenant_ignore: IgnoreReason = IgnoreReason.NOTIMPLEMENTED
    tenant_perm: str = None


TENANT_CHECKS: Mapping[str, TestData] = {
    field_id('Mutation', 'DisableDataSubscriptions'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'addConsumptionRoleToEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'addRedshiftDatasetTables'): TestData(tenant_perm=MANAGE_REDSHIFT_DATASETS),
    field_id('Mutation', 'addSharedItem'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'approveDashboardShare'): TestData(tenant_perm=MANAGE_DASHBOARDS),
    field_id('Mutation', 'approveShareExtension'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'approveShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'approveTermAssociation'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'archiveOrganization'): TestData(tenant_perm=MANAGE_ORGANIZATIONS),
    field_id('Mutation', 'batchMetadataFormFieldUpdates'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'cancelShareExtension'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'createCategory'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'createDataPipeline'): TestData(tenant_perm=MANAGE_PIPELINES),
    field_id('Mutation', 'createDataPipelineEnvironment'): TestData(tenant_perm=MANAGE_PIPELINES),
    field_id('Mutation', 'createDataset'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'createDatasetStorageLocation'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'createEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'createGlossary'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'createMetadataForm'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'createMetadataFormFields'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'createMetadataFormVersion'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'createNetwork'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'createOmicsRun'): TestData(tenant_perm=MANAGE_OMICS_RUNS),
    field_id('Mutation', 'createOrganization'): TestData(tenant_perm=MANAGE_ORGANIZATIONS),
    field_id('Mutation', 'createSagemakerNotebook'): TestData(tenant_perm=MANAGE_NOTEBOOKS),
    field_id('Mutation', 'createSagemakerStudioUser'): TestData(tenant_perm=MANAGE_SGMSTUDIO_USERS),
    field_id('Mutation', 'createShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'createTableDataFilter'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'createTerm'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'createWorksheet'): TestData(tenant_perm=MANAGE_WORKSHEETS),
    field_id('Mutation', 'deleteCategory'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'deleteDashboard'): TestData(tenant_perm=MANAGE_DASHBOARDS),
    field_id('Mutation', 'deleteDataPipeline'): TestData(tenant_perm=MANAGE_PIPELINES),
    field_id('Mutation', 'deleteDataPipelineEnvironment'): TestData(tenant_perm=MANAGE_PIPELINES),
    field_id('Mutation', 'deleteDataset'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'deleteDatasetStorageLocation'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'deleteDatasetTable'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'deleteEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'deleteGlossary'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'deleteMetadataForm'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'deleteMetadataFormField'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'deleteMetadataFormVersion'): TestData(tenant_perm=MANAGE_METADATA_FORMS),
    field_id('Mutation', 'deleteNetwork'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'deleteOmicsRun'): TestData(tenant_perm=MANAGE_OMICS_RUNS),
    field_id('Mutation', 'deleteRedshiftDataset'): TestData(tenant_perm=MANAGE_REDSHIFT_DATASETS),
    field_id('Mutation', 'deleteRedshiftDatasetTable'): TestData(tenant_perm=MANAGE_REDSHIFT_DATASETS),
    field_id('Mutation', 'deleteSagemakerNotebook'): TestData(tenant_perm=MANAGE_NOTEBOOKS),
    field_id('Mutation', 'deleteSagemakerStudioUser'): TestData(tenant_perm=MANAGE_SGMSTUDIO_USERS),
    field_id('Mutation', 'deleteShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'deleteTableDataFilter'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'deleteTerm'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'deleteWorksheet'): TestData(tenant_perm=MANAGE_WORKSHEETS),
    field_id('Mutation', 'dismissTermAssociation'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'enableDataSubscriptions'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'generateDatasetAccessToken'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'importDashboard'): TestData(tenant_perm=MANAGE_DASHBOARDS),
    field_id('Mutation', 'importDataset'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'importRedshiftDataset'): TestData(tenant_perm=MANAGE_REDSHIFT_DATASETS),
    field_id('Mutation', 'inviteGroupOnEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'inviteGroupToOrganization'): TestData(tenant_perm=MANAGE_ORGANIZATIONS),
    field_id('Mutation', 'reApplyItemsShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'reApplyShareObjectItemsOnDataset'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'rejectDashboardShare'): TestData(tenant_perm=MANAGE_DASHBOARDS),
    field_id('Mutation', 'rejectShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'removeConsumptionRoleFromEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'removeGroupFromEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'removeGroupFromOrganization'): TestData(tenant_perm=MANAGE_ORGANIZATIONS),
    field_id('Mutation', 'removeShareItemFilter'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'removeSharedItem'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'requestDashboardShare'): TestData(tenant_perm=MANAGE_DASHBOARDS),
    field_id('Mutation', 'revokeItemsShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'startDatasetProfilingRun'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'startGlueCrawler'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'startSagemakerNotebook'): TestData(tenant_perm=MANAGE_NOTEBOOKS),
    field_id('Mutation', 'stopSagemakerNotebook'): TestData(tenant_perm=MANAGE_NOTEBOOKS),
    field_id('Mutation', 'submitShareExtension'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'submitShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'syncDatasetTableColumns'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'syncTables'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'updateCategory'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'updateConsumptionRole'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'updateDashboard'): TestData(tenant_perm=MANAGE_DASHBOARDS),
    field_id('Mutation', 'updateDataPipeline'): TestData(tenant_perm=MANAGE_PIPELINES),
    field_id('Mutation', 'updateDataPipelineEnvironment'): TestData(tenant_perm=MANAGE_PIPELINES),
    field_id('Mutation', 'updateDataset'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'updateDatasetStorageLocation'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'updateDatasetTable'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'updateDatasetTableColumn'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'updateEnvironment'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'updateGlossary'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'updateGroupEnvironmentPermissions'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'updateKeyValueTags'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'updateOrganization'): TestData(tenant_perm=MANAGE_ORGANIZATIONS),
    field_id('Mutation', 'updateOrganizationGroup'): TestData(tenant_perm=MANAGE_ORGANIZATIONS),
    field_id('Mutation', 'updateRedshiftDataset'): TestData(tenant_perm=MANAGE_REDSHIFT_DATASETS),
    field_id('Mutation', 'updateRedshiftDatasetTable'): TestData(tenant_perm=MANAGE_REDSHIFT_DATASETS),
    field_id('Mutation', 'updateShareExpirationPeriod'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'updateShareExtensionReason'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'updateShareItemFilters'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'updateShareRejectReason'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'updateShareRequestReason'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Mutation', 'updateStack'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Mutation', 'updateTerm'): TestData(tenant_perm=MANAGE_GLOSSARIES),
    field_id('Mutation', 'updateWorksheet'): TestData(tenant_perm=MANAGE_WORKSHEETS),
    field_id('Mutation', 'verifyDatasetShareObjects'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Mutation', 'verifyItemsShareObject'): TestData(tenant_perm=MANAGE_SHARES),
    field_id('Query', 'countDeletedNotifications'): TestData(),
    field_id('Query', 'countReadNotifications'): TestData(),
    field_id('Query', 'countUnreadNotifications'): TestData(),
    field_id('Query', 'countUpVotes'): TestData(),
    field_id('Query', 'generateEnvironmentAccessToken'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Query', 'getAttachedMetadataForm'): TestData(),
    field_id('Query', 'getAuthorSession'): TestData(),
    field_id('Query', 'getCDKExecPolicyPresignedUrl'): TestData(),
    field_id('Query', 'getConsumptionRolePolicies'): TestData(),
    field_id('Query', 'getDashboard'): TestData(),
    field_id('Query', 'getDataPipeline'): TestData(),
    field_id('Query', 'getDataPipelineCredsLinux'): TestData(),
    field_id('Query', 'getDataset'): TestData(),
    field_id('Query', 'getDatasetAssumeRoleUrl'): TestData(tenant_perm=MANAGE_DATASETS),
    field_id('Query', 'getDatasetPresignedUrl'): TestData(),
    field_id('Query', 'getDatasetSharedAssumeRoleUrl'): TestData(),
    field_id('Query', 'getDatasetStorageLocation'): TestData(),
    field_id('Query', 'getDatasetTable'): TestData(),
    field_id('Query', 'getDatasetTableProfilingRun'): TestData(),
    field_id('Query', 'getEntityMetadataFormPermissions'): TestData(),
    field_id('Query', 'getEnvironment'): TestData(),
    field_id('Query', 'getEnvironmentAssumeRoleUrl'): TestData(tenant_perm=MANAGE_ENVIRONMENTS),
    field_id('Query', 'getEnvironmentMLStudioDomain'): TestData(),
    field_id('Query', 'getFeed'): TestData(),
    field_id('Query', 'getGlossary'): TestData(),
    field_id('Query', 'getGroup'): TestData(),
    field_id('Query', 'getGroupsForUser'): TestData(),
    field_id('Query', 'getMaintenanceWindowStatus'): TestData(),
    field_id('Query', 'getMetadataForm'): TestData(),
    field_id('Query', 'getMonitoringDashboardId'): TestData(),
    field_id('Query', 'getMonitoringVPCConnectionId'): TestData(),
    field_id('Query', 'getOmicsWorkflow'): TestData(),
    field_id('Query', 'getOrganization'): TestData(),
    field_id('Query', 'getPivotRoleExternalId'): TestData(),
    field_id('Query', 'getPivotRoleName'): TestData(),
    field_id('Query', 'getPivotRolePresignedUrl'): TestData(),
    field_id('Query', 'getPlatformAuthorSession'): TestData(),
    field_id('Query', 'getPlatformReaderSession'): TestData(),
    field_id('Query', 'getReaderSession'): TestData(),
    field_id('Query', 'getRedshiftDataset'): TestData(),
    field_id('Query', 'getRedshiftDatasetTable'): TestData(),
    field_id('Query', 'getRedshiftDatasetTableColumns'): TestData(),
    field_id('Query', 'getS3ConsumptionData'): TestData(),
    field_id('Query', 'getSagemakerNotebook'): TestData(),
    field_id('Query', 'getSagemakerNotebookPresignedUrl'): TestData(tenant_perm=MANAGE_NOTEBOOKS),
    field_id('Query', 'getSagemakerStudioUser'): TestData(),
    field_id('Query', 'getSagemakerStudioUserPresignedUrl'): TestData(tenant_perm=MANAGE_SGMSTUDIO_USERS),
    field_id('Query', 'getShare'): TestData(),
    field_id('Query', 'getShareItemDataFilters'): TestData(),
    field_id('Query', 'getShareLogs'): TestData(),
    field_id('Query', 'getShareObject'): TestData(),
    field_id('Query', 'getShareRequestsFromMe'): TestData(),
    field_id('Query', 'getShareRequestsToMe'): TestData(),
    field_id('Query', 'getSharedDatasetTables'): TestData(),
    field_id('Query', 'getStack'): TestData(),
    field_id('Query', 'getStackLogs'): TestData(),
    field_id('Query', 'getTrustAccount'): TestData(),
    field_id('Query', 'getVote'): TestData(),
    field_id('Query', 'getWorksheet'): TestData(),
    field_id('Query', 'listAllConsumptionRoles'): TestData(),
    field_id('Query', 'listAllEnvironmentConsumptionRoles'): TestData(),
    field_id('Query', 'listAllEnvironmentGroups'): TestData(),
    field_id('Query', 'listAllGroups'): TestData(),
    field_id('Query', 'listAttachedMetadataForms'): TestData(),
    field_id('Query', 'listConnectionGroupNoPermissions'): TestData(),
    field_id('Query', 'listConnectionGroupPermissions'): TestData(),
    field_id('Query', 'listDashboardShares'): TestData(),
    field_id('Query', 'listDataPipelines'): TestData(),
    field_id('Query', 'listDatasetTableColumns'): TestData(),
    field_id('Query', 'listDatasetTableProfilingRuns'): TestData(),
    field_id('Query', 'listDatasetTables'): TestData(),
    field_id('Query', 'listDatasets'): TestData(),
    field_id('Query', 'listDatasetsCreatedInEnvironment'): TestData(),
    field_id('Query', 'listEntityMetadataForms'): TestData(),
    field_id('Query', 'listEnvironmentConsumptionRoles'): TestData(),
    field_id('Query', 'listEnvironmentGroupInvitationPermissions'): TestData(),
    field_id('Query', 'listEnvironmentGroups'): TestData(),
    field_id('Query', 'listEnvironmentInvitedGroups'): TestData(),
    field_id('Query', 'listEnvironmentNetworks'): TestData(),
    field_id('Query', 'listEnvironmentRedshiftConnections'): TestData(),
    field_id('Query', 'listEnvironments'): TestData(),
    field_id('Query', 'listGlossaries'): TestData(),
    field_id('Query', 'listGroups'): TestData(),
    field_id('Query', 'listInviteOrganizationPermissionsWithDescriptions'): TestData(),
    field_id('Query', 'listKeyValueTags'): TestData(),
    field_id('Query', 'listMetadataFormVersions'): TestData(),
    field_id('Query', 'listNotifications'): TestData(),
    field_id('Query', 'listOmicsRuns'): TestData(),
    field_id('Query', 'listOmicsWorkflows'): TestData(),
    field_id('Query', 'listOrganizationGroupPermissions'): TestData(),
    field_id('Query', 'listOrganizationGroups'): TestData(),
    field_id('Query', 'listOrganizations'): TestData(),
    field_id('Query', 'listOwnedDatasets'): TestData(),
    field_id('Query', 'listRedshiftConnectionSchemas'): TestData(),
    field_id('Query', 'listRedshiftDatasetTables'): TestData(),
    field_id('Query', 'listRedshiftSchemaDatasetTables'): TestData(),
    field_id('Query', 'listRedshiftSchemaTables'): TestData(),
    field_id('Query', 'listS3DatasetsOwnedByEnvGroup'): TestData(),
    field_id('Query', 'listS3DatasetsSharedWithEnvGroup'): TestData(),
    field_id('Query', 'listSagemakerNotebooks'): TestData(),
    field_id('Query', 'listSagemakerStudioUsers'): TestData(),
    field_id('Query', 'listSharedDatasetTableColumns'): TestData(),
    field_id('Query', 'listTableDataFilters'): TestData(),
    field_id('Query', 'listTableDataFiltersByAttached'): TestData(),
    field_id('Query', 'listTenantGroups'): TestData(),
    field_id('Query', 'listTenantPermissions'): TestData(),
    field_id('Query', 'listUserMetadataForms'): TestData(),
    field_id('Query', 'listUsersForGroup'): TestData(),
    field_id('Query', 'listValidEnvironments'): TestData(),
    field_id('Query', 'listWorksheets'): TestData(),
    field_id('Query', 'previewTable'): TestData(),
    field_id('Query', 'queryEnums'): TestData(),
    field_id('Query', 'runAthenaSqlQuery'): TestData(),
    field_id('Query', 'searchDashboards'): TestData(),
    field_id('Query', 'searchEnvironmentDataItems'): TestData(),
    field_id('Query', 'searchGlossary'): TestData(),
    # Admin actions
    field_id('Mutation', 'updateGroupTenantPermissions'): TestData(tenant_ignore=IgnoreReason.ADMIN),
    field_id('Mutation', 'updateSSMParameter'): TestData(tenant_ignore=IgnoreReason.ADMIN),
    field_id('Mutation', 'createQuicksightDataSourceSet'): TestData(tenant_ignore=IgnoreReason.ADMIN),
    field_id('Mutation', 'startMaintenanceWindow'): TestData(tenant_ignore=IgnoreReason.ADMIN),
    field_id('Mutation', 'stopMaintenanceWindow'): TestData(tenant_ignore=IgnoreReason.ADMIN),
    field_id('Mutation', 'startReindexCatalog'): TestData(tenant_ignore=IgnoreReason.ADMIN),
    # Support-related actions
    field_id('Mutation', 'markNotificationAsRead'): TestData(tenant_ignore=IgnoreReason.SUPPORT),
    field_id('Mutation', 'deleteNotification'): TestData(tenant_ignore=IgnoreReason.SUPPORT),
    field_id('Mutation', 'postFeedMessage'): TestData(tenant_ignore=IgnoreReason.FEED),
    field_id('Mutation', 'upVote'): TestData(tenant_ignore=IgnoreReason.VOTES),
    # Backport-related actions
    field_id('Mutation', 'createAttachedMetadataForm'): TestData(tenant_ignore=IgnoreReason.BACKPORT),
    field_id('Mutation', 'deleteAttachedMetadataForm'): TestData(tenant_ignore=IgnoreReason.BACKPORT),
    field_id('Mutation', 'createRedshiftConnection'): TestData(tenant_ignore=IgnoreReason.BACKPORT),
    field_id('Mutation', 'deleteRedshiftConnection'): TestData(tenant_ignore=IgnoreReason.BACKPORT),
    field_id('Mutation', 'addConnectionGroupPermission'): TestData(tenant_ignore=IgnoreReason.BACKPORT),
    field_id('Mutation', 'deleteConnectionGroupPermission'): TestData(tenant_ignore=IgnoreReason.BACKPORT),
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
    tdata = TENANT_CHECKS[fid]
    msg = f'{fid} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    expected_perm = tdata.tenant_perm
    if not expected_perm:
        pytest.skip(msg + f' Reason: {tdata.tenant_ignore.value}')
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
