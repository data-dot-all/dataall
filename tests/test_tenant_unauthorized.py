from unittest.mock import MagicMock, patch
import pytest
from assertpy import assert_that
from dataall.base.api import bootstrap
from dataall.base.loader import load_modules, ImportMode
from dataall.base.context import RequestContext
from dataall.base.db.exceptions import TenantUnauthorized
import inspect


load_modules(modes={ImportMode.API})

OPT_OUT_MUTATIONS = {
    'Mutation.updateGroupTenantPermissions': 'admin action. No need for tenant permission check',
    'Mutation.updateSSMParameter': 'admin action. No need for tenant permission check',
    'Mutation.createQuicksightDataSourceSet': 'admin action. No need for tenant permission check',
    'Mutation.startMaintenanceWindow': 'admin action. No need for tenant permission check',
    'Mutation.stopMaintenanceWindow': 'admin action. No need for tenant permission check',
    'Mutation.startReindexCatalog': 'admin action. No need for tenant permission check',
    'Mutation.markNotificationAsRead': 'tenant permissions do not apply to support notifications',
    'Mutation.deleteNotification': 'tenant permissions do not apply to support notifications',
    'Mutation.postFeedMessage': 'tenant permissions do not apply to support feed messages',
    'Mutation.upVote': 'tenant permissions do not apply to support votes',
    'Mutation.createAttachedMetadataForm': 'outside of this PR to be able to backport to v2.6.2',
    'Mutation.deleteAttachedMetadataForm': 'outside of this PR to be able to backport to v2.6.2',
    'Mutation.createRedshiftConnection': 'outside of this PR to be able to backport to v2.6.2',
    'Mutation.deleteRedshiftConnection': 'outside of this PR to be able to backport to v2.6.2',
    'Mutation.addConnectionGroupPermission': 'outside of this PR to be able to backport to v2.6.2',
    'Mutation.deleteConnectionGroupPermission': 'outside of this PR to be able to backport to v2.6.2',
}

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

ALL_RESOLVERS = {(_type, field) for _type in bootstrap().types for field in _type.fields if field.resolver}


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
        pytest.param(_type, field, id=f'{_type.name}.{field.name}')
        for _type, field in ALL_RESOLVERS
        if _type.name in ['Query', 'Mutation']
    ],
)
@patch('dataall.base.context._request_storage')
def test_unauthorized_tenant_permissions(
    mock_local, _type, field, mock_input_validation, db, userNoTenantPermissions, groupNoTenantPermissions
):
    if _type.name == 'Mutation' and f'{_type.name}.{field.name}' in OPT_OUT_MUTATIONS.keys():
        pytest.skip(f'Skipping test for {field.name}: {OPT_OUT_MUTATIONS[f"{_type.name}.{field.name}"]}')
    if _type.name == 'Query' and f'{_type.name}.{field.name}' not in OPT_IN_QUERIES:
        pytest.skip(f'Skipping test for {field.name}: This Query does not require a tenant permission check.')
    assert_that(field.resolver).is_not_none()
    mock_local.context = RequestContext(
        db, userNoTenantPermissions.username, [groupNoTenantPermissions.groupUri], userNoTenantPermissions
    )
    # Mocking arguments
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    # Assert Unauthorized exception is raised
    assert_that(field.resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation')
