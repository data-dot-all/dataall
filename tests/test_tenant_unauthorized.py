import inspect
import logging
from unittest.mock import MagicMock, patch, ANY

import pytest
from assertpy import assert_that

from dataall.base.api import bootstrap
from dataall.base.context import RequestContext
from dataall.base.db.exceptions import TenantUnauthorized, ResourceUnauthorized
from dataall.core.permissions.services.environment_permissions import GET_ENVIRONMENT
from dataall.core.permissions.services.network_permissions import GET_NETWORK
from dataall.core.permissions.services.organization_permissions import GET_ORGANIZATION
from dataall.modules.datapipelines.services.datapipelines_permissions import GET_PIPELINE
from dataall.modules.s3_datasets.services.dataset_permissions import GET_DATASET, GET_DATASET_TABLE

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


IGNORE_NESTED_RESOLVERS = [
    'AttachedMetadataForm_entityName',
    'AttachedMetadataForm_fields',
    'AttachedMetadataForm_metadataForm',
    'AttachedMetadataFormField_field',
    'AttachedMetadataFormField_hasTenantPermissions',
    'Category_associations',
    'Category_categories',
    'Category_children',
    'Category_stats',
    'Category_terms',
    'Dashboard_terms',
    'Dashboard_upvotes',
    'Dashboard_userRoleForDashboard',
    'DataPipeline_cloneUrlHttp',
    'DataPipeline_developmentEnvironments',
    'DataPipeline_userRoleForPipeline',
    'Dataset_locations',
    'Dataset_owners',
    'Dataset_statistics',
    'Dataset_stewards',
    'Dataset_tables',
    'Dataset_terms',
    'Dataset_userRoleForDataset',
    'DatasetBase_owners',
    'DatasetBase_stewards',
    'DatasetBase_userRoleForDataset',
    'DatasetProfilingRun_results',
    'DatasetProfilingRun_status',
    'DatasetStorageLocation_terms',
    'DatasetTable_columns',
    'DatasetTable_terms',
    'DatasetTableColumn_terms',
    'Environment_organization',
    'Environment_parameters',
    'Environment_userRoleInEnvironment',
    'EnvironmentSimplified_organization',
]

EXPECTED_PERMS = {
    'ConsumptionRole_managedPolicies': GET_ENVIRONMENT,
    'Dashboard_environment': GET_ENVIRONMENT,
    'DataPipeline_environment': GET_ENVIRONMENT,
    'DataPipeline_organization': GET_ORGANIZATION,
    'DataPipeline_stack': GET_PIPELINE,
    'Dataset_environment': GET_ENVIRONMENT,
    'Dataset_stack': GET_DATASET,
    'DatasetBase_environment': GET_ENVIRONMENT,
    'DatasetBase_stack': GET_DATASET,
    'DatasetProfilingRun_dataset': GET_DATASET,
    'DatasetTable_dataset': GET_DATASET,
    'DatasetTable_GlueTableProperties': GET_DATASET_TABLE,
    'Environment_networks': GET_NETWORK,
    'Environment_stack': GET_ENVIRONMENT,
    'EnvironmentSimplified_networks': GET_NETWORK,
}


@patch('dataall.base.aws.sts.SessionHelper.remote_session')
@patch('dataall.core.permissions.services.resource_policy_service.ResourcePolicyService.check_user_resource_permission')
@patch('dataall.base.context._request_storage')
@pytest.mark.parametrize(
    'field',
    [
        pytest.param(field, id=f'{_type.name}_{field.name}')
        for _type, field in ALL_RESOLVERS
        if _type.name not in ['Query', 'Mutation']  # filter out top-level queries (don't print skip)
    ],
)
def test_unauthorized_resource_permissions(
    mock_local,
    mock_check,
    mock_session,
    field,
    request,
):
    msg = (
        f'{request.node.callspec.id} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    )
    if request.node.callspec.id in IGNORE_NESTED_RESOLVERS:
        pytest.skip(msg)
    logging.info(msg)

    assert_that(field.resolver).is_not_none()
    username = 'ausername'
    groups = ['agroup']
    mock_local.context = RequestContext(MagicMock(), username, groups, 'auserid')
    mock_check.side_effect = ResourceUnauthorized(groups, 'test_action', 'test_uri')
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    assert_that(field.resolver).described_as(
        f'resolver code: {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    ).raises(ResourceUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation', 'test_action')
    mock_check.assert_called_once_with(
        session=ANY,
        resource_uri=ANY,
        username=username,
        groups=groups,
        permission_name=EXPECTED_PERMS.get(request.node.callspec.id, 'FOO_TEST_PERM'),
    )
