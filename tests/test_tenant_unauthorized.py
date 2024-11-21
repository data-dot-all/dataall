import inspect
import logging
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
from dataall.modules.datapipelines.services.datapipelines_permissions import GET_PIPELINE
from dataall.modules.s3_datasets.services.dataset_permissions import GET_DATASET, GET_DATASET_TABLE


def resolver_id(type_name, field_name):
    return f'{type_name}_{field_name}'


class IgnoreReason(Enum):
    ADMIN = 'admin action. No need for tenant permission check'
    SUPPORT = 'tenant permissions do not apply to support notifications'
    FEED = 'tenant permissions do not apply to support feed messages'
    VOTES = 'tenant permissions do not apply to support votes'
    BACKPORT = 'outside of this PR to be able to backport to v2.6.2'


def get_resid(type_name: str, field_name: str) -> str:
    return f'{type_name}_{field_name}'


OPT_OUT_MUTATIONS = {
    # Admin actions
    get_resid('Mutation', 'updateGroupTenantPermissions'): IgnoreReason.ADMIN.value,
    get_resid('Mutation', 'updateSSMParameter'): IgnoreReason.ADMIN.value,
    get_resid('Mutation', 'createQuicksightDataSourceSet'): IgnoreReason.ADMIN.value,
    get_resid('Mutation', 'startMaintenanceWindow'): IgnoreReason.ADMIN.value,
    get_resid('Mutation', 'stopMaintenanceWindow'): IgnoreReason.ADMIN.value,
    get_resid('Mutation', 'startReindexCatalog'): IgnoreReason.ADMIN.value,

    # Support-related actions
    get_resid('Mutation', 'markNotificationAsRead'): IgnoreReason.SUPPORT.value,
    get_resid('Mutation', 'deleteNotification'): IgnoreReason.SUPPORT.value,
    get_resid('Mutation', 'postFeedMessage'): IgnoreReason.FEED.value,
    get_resid('Mutation', 'upVote'): IgnoreReason.VOTES.value,

    # Backport-related actions
    get_resid('Mutation', 'createAttachedMetadataForm'): IgnoreReason.BACKPORT.value,
    get_resid('Mutation', 'deleteAttachedMetadataForm'): IgnoreReason.BACKPORT.value,
    get_resid('Mutation', 'createRedshiftConnection'): IgnoreReason.BACKPORT.value,
    get_resid('Mutation', 'deleteRedshiftConnection'): IgnoreReason.BACKPORT.value,
    get_resid('Mutation', 'addConnectionGroupPermission'): IgnoreReason.BACKPORT.value,
    get_resid('Mutation', 'deleteConnectionGroupPermission'): IgnoreReason.BACKPORT.value,
}

OPT_IN_QUERIES = [
    get_resid('Query', 'generateEnvironmentAccessToken'),
    get_resid('Query', 'getEnvironmentAssumeRoleUrl'),
    get_resid('Query', 'getSagemakerStudioUserPresignedUrl'),
    get_resid('Query', 'getSagemakerNotebookPresignedUrl'),
    get_resid('Query', 'getDatasetAssumeRoleUrl'),
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
        pytest.param(_type, field, id=get_resid(_type.name, field.name))
        for _type, field in ALL_RESOLVERS
        if _type.name in ['Query', 'Mutation']
    ],
)
@patch('dataall.base.context._request_storage')
def test_unauthorized_tenant_permissions(
    mock_local,
    _type,
    field,
    request,
    mock_input_validation,
    db,
    userNoTenantPermissions,
    groupNoTenantPermissions,
):
    res_id = request.node.callspec.id
    if _type.name == 'Mutation' and res_id in OPT_OUT_MUTATIONS.keys():
        pytest.skip(f'Skipping test for {res_id}: {OPT_OUT_MUTATIONS[res_id]}')
    if _type.name == 'Query' and res_id not in OPT_IN_QUERIES:
        pytest.skip(f'Skipping test for {res_id}: This Query does not require a tenant permission check.')
    assert_that(field.resolver).is_not_none()
    mock_local.context = RequestContext(
        db, userNoTenantPermissions.username, [groupNoTenantPermissions.groupUri], userNoTenantPermissions
    )
    # Mocking arguments
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    # Assert Unauthorized exception is raised
    assert_that(field.resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation')


SKIP_MARK = 'SKIP_MARK'

NESTED_RESOLVERS_EXPECTED_PERMS = {
    # AttachedMetadataForm related
    get_resid('AttachedMetadataFormField', 'field'): SKIP_MARK,
    get_resid('AttachedMetadataFormField', 'hasTenantPermissions'): SKIP_MARK,
    get_resid('AttachedMetadataForm', 'entityName'): SKIP_MARK,
    get_resid('AttachedMetadataForm', 'fields'): SKIP_MARK,
    get_resid('AttachedMetadataForm', 'metadataForm'): SKIP_MARK,

    # Category related
    get_resid('Category', 'associations'): SKIP_MARK,
    get_resid('Category', 'categories'): SKIP_MARK,
    get_resid('Category', 'children'): SKIP_MARK,
    get_resid('Category', 'stats'): SKIP_MARK,
    get_resid('Category', 'terms'): SKIP_MARK,

    # ConsumptionRole related
    get_resid('ConsumptionRole', 'managedPolicies'): GET_ENVIRONMENT,

    # Dashboard related
    get_resid('Dashboard', 'environment'): GET_ENVIRONMENT,
    get_resid('Dashboard', 'terms'): SKIP_MARK,
    get_resid('Dashboard', 'upvotes'): SKIP_MARK,
    get_resid('Dashboard', 'userRoleForDashboard'): SKIP_MARK,

    # DataPipeline related
    get_resid('DataPipeline', 'cloneUrlHttp'): SKIP_MARK,
    get_resid('DataPipeline', 'developmentEnvironments'): SKIP_MARK,
    get_resid('DataPipeline', 'environment'): GET_ENVIRONMENT,
    get_resid('DataPipeline', 'organization'): GET_ORGANIZATION,
    get_resid('DataPipeline', 'stack'): GET_PIPELINE,
    get_resid('DataPipeline', 'userRoleForPipeline'): SKIP_MARK,

    # Dataset related
    get_resid('DatasetBase', 'environment'): GET_ENVIRONMENT,
    get_resid('DatasetBase', 'owners'): SKIP_MARK,
    get_resid('DatasetBase', 'stack'): GET_DATASET,
    get_resid('DatasetBase', 'stewards'): SKIP_MARK,
    get_resid('DatasetBase', 'userRoleForDataset'): SKIP_MARK,

    # Dataset Profiling related
    get_resid('DatasetProfilingRun', 'dataset'): GET_DATASET,
    get_resid('DatasetProfilingRun', 'results'): SKIP_MARK,
    get_resid('DatasetProfilingRun', 'status'): SKIP_MARK,

    # Dataset Storage and Table related
    get_resid('DatasetStorageLocation', 'terms'): SKIP_MARK,
    get_resid('DatasetTableColumn', 'terms'): SKIP_MARK,
    get_resid('DatasetTable', 'GlueTableProperties'): GET_DATASET_TABLE,
    get_resid('DatasetTable', 'columns'): SKIP_MARK,
    get_resid('DatasetTable', 'dataset'): GET_DATASET,
    get_resid('DatasetTable', 'terms'): SKIP_MARK,

    # Dataset specific
    get_resid('Dataset', 'environment'): GET_ENVIRONMENT,
    get_resid('Dataset', 'locations'): SKIP_MARK,
    get_resid('Dataset', 'owners'): SKIP_MARK,
    get_resid('Dataset', 'stack'): GET_DATASET,
    get_resid('Dataset', 'statistics'): SKIP_MARK,
    get_resid('Dataset', 'stewards'): SKIP_MARK,
    get_resid('Dataset', 'tables'): SKIP_MARK,
    get_resid('Dataset', 'terms'): SKIP_MARK,
    get_resid('Dataset', 'userRoleForDataset'): SKIP_MARK,

    # Environment related
    get_resid('EnvironmentSimplified', 'networks'): GET_NETWORK,
    get_resid('EnvironmentSimplified', 'organization'): SKIP_MARK,
    get_resid('Environment', 'networks'): GET_NETWORK,
    get_resid('Environment', 'organization'): SKIP_MARK,
    get_resid('Environment', 'parameters'): SKIP_MARK,
    get_resid('Environment', 'stack'): GET_ENVIRONMENT,
    get_resid('Environment', 'userRoleInEnvironment'): SKIP_MARK,

    # Feed and Glossary related
    get_resid('Feed', 'messages'): SKIP_MARK,
    get_resid('GlossaryTermLink', 'target'): SKIP_MARK,
    get_resid('GlossaryTermLink', 'term'): SKIP_MARK,
    get_resid('Glossary', 'associations'): SKIP_MARK,
    get_resid('Glossary', 'categories'): SKIP_MARK,
    get_resid('Glossary', 'children'): SKIP_MARK,
    get_resid('Glossary', 'stats'): SKIP_MARK,
    get_resid('Glossary', 'tree'): SKIP_MARK,
    get_resid('Glossary', 'userRoleForGlossary'): SKIP_MARK,

    # Group and Metadata related
    get_resid('Group', 'environmentPermissions'): SKIP_MARK,
    get_resid('Group', 'tenantPermissions'): SKIP_MARK,
    get_resid('MetadataFormField', 'glossaryNodeName'): SKIP_MARK,
    get_resid('MetadataFormSearchResult', 'hasTenantPermissions'): SKIP_MARK,
    get_resid('MetadataForm', 'fields'): SKIP_MARK,
    get_resid('MetadataForm', 'homeEntityName'): SKIP_MARK,
    get_resid('MetadataForm', 'userRole'): SKIP_MARK,

    # Omics related
    get_resid('OmicsRun', 'environment'): GET_ENVIRONMENT,
    get_resid('OmicsRun', 'organization'): GET_ORGANIZATION,
    get_resid('OmicsRun', 'status'): SKIP_MARK,
    get_resid('OmicsRun', 'workflow'): SKIP_MARK,

    # Organization related
    get_resid('Organization', 'environments'): GET_ORGANIZATION,
    get_resid('Organization', 'stats'): SKIP_MARK,
    get_resid('Organization', 'userRoleInOrganization'): SKIP_MARK,
}


@patch('dataall.base.aws.sts.SessionHelper.remote_session')
@patch('dataall.core.permissions.services.resource_policy_service.ResourcePolicyService.check_user_resource_permission')
@patch('dataall.base.context._request_storage')
@pytest.mark.parametrize(
    'field',
    [
        pytest.param(field, id=get_resid(_type.name, field.name))
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
    res_id = request.node.callspec.id
    expected_perm = NESTED_RESOLVERS_EXPECTED_PERMS.get(res_id, 'FOO_TEST_PERM')
    msg = f'{res_id} -> {field.resolver.__code__.co_filename}:{field.resolver.__code__.co_firstlineno}'
    if expected_perm in SKIP_MARK:
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
        permission_name=expected_perm,
    )
