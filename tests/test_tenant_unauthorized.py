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
OPT_OUT_MUTATIONS = [
    'Mutation.updateGroupTenantPermissions',  #  admin action. No need for tenant permission check
    'Mutation.updateSSMParameter',  #  admin action. No need for tenant permission check
    'Mutation.createQuicksightDataSourceSet',  #  admin action. No need for tenant permission check
    'Mutation.startMaintenanceWindow',  #  admin action. No need for tenant permission check
    'Mutation.stopMaintenanceWindow',  #  admin action. No need for tenant permission check
    'Mutation.startReindexCatalog',  #  admin action. No need for tenant permission check
    'Mutation.markNotificationAsRead',  #  tenant permissions do not apply to user personal notifications.
    'Mutation.deleteNotification',  #  tenant permissions do not apply to user personal notifications.
    'Mutation.postFeedMessage',  #  tenant permissions do not apply to user personal feed comments.
    'Mutation.upVote',  #  tenant permissions do not apply to user personal up votes.
    'Mutation.createShareObject',  #  follow-up PR. ADD MANAGE_SHARE permission
    'Mutation.deleteShareObject',
    'Mutation.cancelShareExtension',
    'Mutation.addSharedItem',
    'Mutation.removeSharedItem',
    'Mutation.submitShareObject',
    'Mutation.submitShareExtension',
    'Mutation.approveShareObject',
    'Mutation.approveShareExtension',
    'Mutation.rejectShareObject',
    'Mutation.revokeItemsShareObject',
    'Mutation.verifyItemsShareObject',
    'Mutation.reApplyItemsShareObject',
    'Mutation.updateShareRejectReason',
    'Mutation.updateShareExpirationPeriod',
    'Mutation.updateShareExtensionReason',
    'Mutation.updateShareRequestReason',
    'Mutation.updateShareItemFilters',
    'Mutation.removeShareItemFilter',
    'Mutation.createAttachedMetadataForm',  #  outside of this PR to be able to backport to v2.6.2
    'Mutation.deleteAttachedMetadataForm',  #  outside of this PR to be able to backport to v2.6.2
    'Mutation.createRedshiftConnection',  #  outside of this PR to be able to backport to v2.6.2
    'Mutation.deleteRedshiftConnection',  #  outside of this PR to be able to backport to v2.6.2
    'Mutation.addConnectionGroupPermission',  #  outside of this PR to be able to backport to v2.6.2
    'Mutation.deleteConnectionGroupPermission',  #  outside of this PR to be able to backport to v2.6.2
]

OPT_IN_QUERIES = [
    'Query.generateEnvironmentAccessToken',
    'Query.getEnvironmentAssumeRoleUrl',
    'Query.getSagemakerStudioUserPresignedUrl',
    'Query.getSagemakerNotebookPresignedUrl',
    'Query.getDatasetAssumeRoleUrl',
    'Query.getDatasetPresignedUrl',
    'Query.getAuthorSession',
    'Query.getDatasetSharedAssumeRoleUrl',
    'Query.runAthenaSqlQuery',
]

ALL_QUERIES = {
    f'{_type.name}.{field.name}': field.resolver
    for _type in bootstrap().types
    for field in _type.fields
    if field.resolver and _type.name == 'Query'
}

ALL_MUTATIONS = {
    f'{_type.name}.{field.name}': field.resolver
    for _type in bootstrap().types
    for field in _type.fields
    if field.resolver and _type.name == 'Mutation'
}


@pytest.mark.parametrize(
    'name,field_resolver',
    [(key, value) for key, value in ALL_MUTATIONS.items() if key not in OPT_OUT_MUTATIONS]
    + [(name, ALL_QUERIES.get(name, None)) for name in OPT_IN_QUERIES],
)
def test_unauthorized_tenant_permissions(
    name, field_resolver, mocker, db, userNoTenantPermissions, groupNoTenantPermissions
):
    assert_that(field_resolver).is_not_none()
    mock_local = MagicMock()
    mock_local.context = RequestContext(
        db, userNoTenantPermissions.username, [groupNoTenantPermissions.groupUri], userNoTenantPermissions
    )
    with mocker.patch('dataall.base.context._request_storage', mock_local):
        ## Creation mocks
        mocker.patch('dataall.modules.mlstudio.api.resolvers.RequestValidator', MagicMock())
        mocker.patch(
            'dataall.modules.mlstudio.services.mlstudio_service.SagemakerStudioCreationRequest.from_dict', MagicMock()
        )
        mocker.patch('dataall.modules.notebooks.api.resolvers.RequestValidator', MagicMock())
        mocker.patch(
            'dataall.modules.notebooks.services.notebook_service.NotebookCreationRequest.from_dict', MagicMock()
        )
        mocker.patch('dataall.modules.s3_datasets.api.profiling.resolvers._validate_uri', MagicMock())
        mocker.patch('dataall.modules.s3_datasets.api.storage_location.resolvers._validate_input', MagicMock())
        mocker.patch('dataall.modules.s3_datasets.api.dataset.resolvers.RequestValidator', MagicMock())
        mocker.patch(
            'dataall.core.stacks.db.target_type_repositories.TargetType.get_resource_tenant_permission_name',
            return_value='MANAGE_ENVIRONMENTS',
        )
        # Mocking arguments
        iargs = {arg: MagicMock() for arg in inspect.signature(field_resolver).parameters.keys()}
        # Assert Unauthorized exception is raised
        assert_that(field_resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains(
            'UnauthorizedOperation'
        )
