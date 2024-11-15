from unittest.mock import MagicMock
import pytest
from assertpy import assert_that
from dataall.base.api import bootstrap
from dataall.base.loader import load_modules, ImportMode
from dataall.base.context import RequestContext
from dataall.base.db.exceptions import TenantUnauthorized
import inspect


load_modules(modes={ImportMode.API})

## Those Mutations that are commented out either need to be assessed or fixed. They might not need the check of permissions
## or they might require additional work to add permissions or to adjust the tests.

CHECK_PERMS = [
    # 'Mutation.updateGroupTenantPermissions', ---> admin action. No need for tenant permission check
    # 'Mutation.updateSSMParameter', ---> admin action. No need for tenant permission check
    'Mutation.createOrganization',
    'Mutation.updateOrganization',
    'Mutation.archiveOrganization',
    'Mutation.inviteGroupToOrganization',
    'Mutation.updateOrganizationGroup',
    'Mutation.removeGroupFromOrganization',
    'Mutation.createNetwork',
    'Mutation.deleteNetwork',
    'Mutation.createEnvironment',
    'Mutation.updateEnvironment',
    'Mutation.inviteGroupOnEnvironment',
    'Mutation.addConsumptionRoleToEnvironment',
    'Mutation.updateGroupEnvironmentPermissions',
    'Mutation.removeGroupFromEnvironment',
    'Mutation.removeConsumptionRoleFromEnvironment',
    'Mutation.deleteEnvironment',
    'Mutation.enableDataSubscriptions',
    'Mutation.DisableDataSubscriptions',
    'Mutation.updateConsumptionRole',
    'Query.generateEnvironmentAccessToken',
    'Query.getEnvironmentAssumeRoleUrl',
    # 'Mutation.updateStack', ---> fix for nested fields
    # 'Mutation.updateKeyValueTags', ---> fix for nested fields
    'Mutation.createSagemakerStudioUser',
    'Mutation.deleteSagemakerStudioUser',
    'Query.getSagemakerStudioUserPresignedUrl',
    'Mutation.createSagemakerNotebook',
    'Mutation.startSagemakerNotebook',
    'Mutation.stopSagemakerNotebook',
    'Mutation.deleteSagemakerNotebook',
    # 'Query.getSagemakerNotebookPresignedUrl'
    'Mutation.createMetadataForm',
    'Mutation.createMetadataFormVersion',
    # 'Mutation.createAttachedMetadataForm',
    'Mutation.deleteMetadataForm',
    'Mutation.deleteMetadataFormVersion',
    # 'Mutation.deleteAttachedMetadataForm',
    'Mutation.createMetadataFormFields',
    'Mutation.deleteMetadataFormField',
    'Mutation.batchMetadataFormFieldUpdates',
    # 'Mutation.startMaintenanceWindow',  ---> admin action. No need for tenant permission check
    # 'Mutation.stopMaintenanceWindow',  ---> admin action. No need for tenant permission check
    # 'Mutation.markNotificationAsRead',
    # 'Mutation.deleteNotification',
    'Mutation.createGlossary',
    'Mutation.updateGlossary',
    'Mutation.deleteGlossary',
    'Mutation.createCategory',
    'Mutation.updateCategory',
    'Mutation.deleteCategory',
    'Mutation.createTerm',
    'Mutation.updateTerm',
    'Mutation.deleteTerm',
    'Mutation.approveTermAssociation',
    'Mutation.dismissTermAssociation',
    # 'Mutation.startReindexCatalog',  ---> admin action. No need for tenant permission check
    # 'Mutation.postFeedMessage',
    # 'Mutation.createShareObject',
    # 'Mutation.deleteShareObject',
    # 'Mutation.cancelShareExtension',
    # 'Mutation.addSharedItem',
    # 'Mutation.removeSharedItem',
    # 'Mutation.submitShareObject',
    # 'Mutation.submitShareExtension',
    # 'Mutation.approveShareObject',
    # 'Mutation.approveShareExtension',
    # 'Mutation.rejectShareObject',
    # 'Mutation.revokeItemsShareObject',
    # 'Mutation.verifyItemsShareObject',
    # 'Mutation.reApplyItemsShareObject',
    # 'Mutation.updateShareRejectReason',
    # 'Mutation.updateShareExpirationPeriod',
    # 'Mutation.updateShareExtensionReason',
    # 'Mutation.updateShareRequestReason',
    # 'Mutation.updateShareItemFilters',
    # 'Mutation.removeShareItemFilter',
    # 'Mutation.upVote',
    # 'Mutation.syncDatasetTableColumns',
    # 'Mutation.updateDatasetTableColumn',
    # 'Mutation.startDatasetProfilingRun',
    # 'Mutation.createDatasetStorageLocation',
    # 'Mutation.updateDatasetStorageLocation',
    # 'Mutation.deleteDatasetStorageLocation',
    # 'Mutation.createDataset',
    # 'Mutation.updateDataset',
    # 'Mutation.generateDatasetAccessToken',
    'Mutation.deleteDataset',
    # 'Mutation.importDataset',
    # 'Mutation.startGlueCrawler',
    'Mutation.updateDatasetTable',
    'Mutation.deleteDatasetTable',
    'Mutation.syncTables',
    # 'Mutation.createTableDataFilter',
    # 'Mutation.deleteTableDataFilter',
    # 'Query.getDatasetAssumeRoleUrl',
    # 'Query.getDatasetPresignedUrl',
    # 'Mutation.createRedshiftConnection',
    # 'Mutation.deleteRedshiftConnection',
    # 'Mutation.addConnectionGroupPermission',
    # 'Mutation.deleteConnectionGroupPermission',
    'Mutation.importRedshiftDataset',
    'Mutation.updateRedshiftDataset',
    'Mutation.deleteRedshiftDataset',
    'Mutation.addRedshiftDatasetTables',
    'Mutation.deleteRedshiftDatasetTable',
    'Mutation.updateRedshiftDatasetTable',
    'Mutation.importDashboard',
    'Mutation.updateDashboard',
    'Mutation.deleteDashboard',
    'Mutation.requestDashboardShare',
    'Mutation.approveDashboardShare',
    'Mutation.rejectDashboardShare',
    # 'Mutation.createQuicksightDataSourceSet',  ---> admin action. No need for tenant permission check
    # 'Query.getAuthorSession',
    'Mutation.verifyDatasetShareObjects',
    'Mutation.reApplyShareObjectItemsOnDataset',
    # 'Query.getDatasetSharedAssumeRoleUrl'
    'Mutation.createWorksheet',
    'Mutation.updateWorksheet',
    'Mutation.deleteWorksheet',
    # 'Query.runAthenaSqlQuery'
]

ALL_RESOLVERS = {
    f'{_type.name}.{field.name}': field.resolver
    for _type in bootstrap().types
    for field in _type.fields
    if field.resolver
}


@pytest.mark.parametrize('name,field_resolver', [(name, ALL_RESOLVERS.get(name, None)) for name in CHECK_PERMS])
def test_unauthorized_tenant_permissions(
    name, field_resolver, mocker, db, userNoTenantPermissions, groupNoTenantPermissions
):
    assert_that(field_resolver).is_not_none()
    mock_local = MagicMock()
    mock_local.context = RequestContext(
        db, userNoTenantPermissions.username, [groupNoTenantPermissions.groupUri], userNoTenantPermissions
    )
    with mocker.patch('dataall.base.context._request_storage', mock_local):
        print(inspect.signature(field_resolver).parameters.keys())
        iargs = {arg: MagicMock() for arg in inspect.signature(field_resolver).parameters.keys()}
        assert_that(field_resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains(
            'UnauthorizedOperation'
        )
