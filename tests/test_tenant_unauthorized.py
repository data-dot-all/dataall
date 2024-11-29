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
from dataall.modules.datapipelines.services.datapipelines_permissions import GET_PIPELINE
from dataall.modules.mlstudio.services.mlstudio_permissions import GET_SGMSTUDIO_USER
from dataall.modules.notebooks.services.notebook_permissions import GET_NOTEBOOK
from dataall.modules.s3_datasets.services.dataset_permissions import GET_DATASET, GET_DATASET_TABLE


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


def field_id(type_name: str, field_name: str) -> str:
    return f'{type_name}_{field_name}'


OPT_OUT_MUTATIONS = {
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

OPT_IN_QUERIES = [
    field_id('Query', 'generateEnvironmentAccessToken'),
    field_id('Query', 'getEnvironmentAssumeRoleUrl'),
    field_id('Query', 'getSagemakerStudioUserPresignedUrl'),
    field_id('Query', 'getSagemakerNotebookPresignedUrl'),
    field_id('Query', 'getDatasetAssumeRoleUrl'),
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
        pytest.param(_type, field, id=field_id(_type.name, field.name))
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
    fid = request.node.callspec.id
    if _type.name == 'Mutation' and (reason := OPT_OUT_MUTATIONS.get(fid)):
        pytest.skip(f'Skipping test for {fid}: {reason}')
    if _type.name == 'Query' and fid not in OPT_IN_QUERIES:
        pytest.skip(f'Skipping test for {fid}: This Query does not require a tenant permission check.')
    assert_that(field.resolver).is_not_none()
    mock_local.context = RequestContext(
        db, userNoTenantPermissions.username, [groupNoTenantPermissions.groupUri], userNoTenantPermissions
    )
    # Mocking arguments
    iargs = {arg: MagicMock() for arg in inspect.signature(field.resolver).parameters.keys()}
    # Assert Unauthorized exception is raised
    assert_that(field.resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation')


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
