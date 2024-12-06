import logging
from inspect import unwrap, getabsfile, getsourcelines, signature
from unittest.mock import MagicMock, patch, ANY

import pytest
from assertpy import assert_that

from dataall.base.api import bootstrap
from dataall.base.context import RequestContext
from dataall.modules.maintenance.api.enums import MaintenanceModes
from tests.permissions import field_id, EXPECTED_RESOLVERS, TARGET_TYPE_PERM

ALL_RESOLVERS = {(_type, field) for _type in bootstrap().types for field in _type.fields if field.resolver}


@pytest.fixture(scope='function')
def common_mocks(mocker):
    mocker.patch('boto3.client').side_effect = RuntimeError('mocked boto3 client')
    mocker.patch('dataall.base.aws.sts.SessionHelper._get_parameter_value')
    mocker.patch('dataall.base.aws.sts.SessionHelper.get_session')
    mocker.patch('dataall.base.aws.sts.SessionHelper.remote_session')
    mocker.patch('dataall.core.permissions.services.tenant_policy_service.RequestValidationService')
    mocker.patch('dataall.modules.mlstudio.api.resolvers.RequestValidator')
    mocker.patch('dataall.modules.mlstudio.services.mlstudio_service.SagemakerStudioCreationRequest.from_dict')
    mocker.patch('dataall.modules.notebooks.api.resolvers.RequestValidator')
    mocker.patch('dataall.modules.notebooks.services.notebook_service.NotebookCreationRequest.from_dict')
    mocker.patch('dataall.modules.redshift_datasets.api.connections.resolvers.RequestValidator')
    mocker.patch('dataall.modules.s3_datasets.api.dataset.resolvers.RequestValidator')
    mocker.patch('dataall.modules.s3_datasets.api.profiling.resolvers._validate_uri')
    mocker.patch('dataall.modules.s3_datasets.api.storage_location.resolvers._validate_input')
    mocker.patch('dataall.modules.shares_base.api.resolvers.RequestValidator')


ALL_PARAMS = [pytest.param(field, id=field_id(_type.name, field.name)) for _type, field in ALL_RESOLVERS]


def test_all_resolvers_have_test_data():
    """
    ensure that all EXPECTED_RESOURCES_PERMS have a corresponding query (to avoid stale entries) and vice versa
    """
    assert_that(ALL_PARAMS).extracting(2).described_as(
        'stale or missing EXPECTED_RESOURCE_PERMS detected'
    ).contains_only(*EXPECTED_RESOLVERS.keys())


def setup_Mutation_deleteOmicsRun(iargs, **kwargs):
    iargs['input'] = {'runUris': [MagicMock()]}


def setup_Mutation_startMaintenanceWindow(iargs, **kwargs):
    iargs['mode'] = MaintenanceModes.READONLY.value


def setup_networks(mock_storage, **kwargs):
    mock_storage.context.db_engine.scoped_session().__enter__().query().filter().all.return_value = [MagicMock()]


setup_EnvironmentSimplified_networks = setup_networks
setup_Environment_networks = setup_networks


def setup_Mutation_upVote(mocker, **kwargs):
    mocker.patch(
        'dataall.modules.vote.services.vote_service.get_vote_type', return_value={'permission': TARGET_TYPE_PERM}
    )


@pytest.mark.parametrize('field', ALL_PARAMS)
@pytest.mark.parametrize(
    'perm_type', ['resource', 'tenant', 'tenant_admin', 'glossary_owner', 'mf_owner', 'notification_recipient']
)
@patch('dataall.base.context._request_storage')
@patch('dataall.modules.notifications.services.notification_service.NotificationAccess.check_recipient')
@patch('dataall.modules.metadata_forms.services.metadata_form_access_service.MetadataFormAccessService.is_owner')
@patch('dataall.modules.catalog.services.glossaries_service.GlossariesResourceAccess.check_owner')
@patch('dataall.core.permissions.services.resource_policy_service.ResourcePolicyService.check_user_resource_permission')
@patch('dataall.core.permissions.services.group_policy_service.GroupPolicyService.check_group_environment_permission')
@patch('dataall.core.permissions.services.tenant_policy_service.TenantPolicyService.check_user_tenant_permission')
@patch('dataall.core.permissions.services.tenant_policy_service.TenantPolicyValidationService.is_tenant_admin')
@patch('dataall.core.stacks.db.target_type_repositories.TargetType.get_resource_read_permission_name')
@patch('dataall.core.stacks.db.target_type_repositories.TargetType.get_resource_update_permission_name')
@patch('dataall.core.stacks.db.target_type_repositories.TargetType.get_resource_tenant_permission_name')
@patch('dataall.modules.feed.api.registry.FeedRegistry.find_permission')
def test_permissions(
    mock_feed_find_perm,
    mock_tenant_perm_name,
    mock_update_perm_name,
    mock_read_perm_name,
    mock_check_tenant_admin,
    mock_check_tenant,
    mock_check_group,
    mock_check_resource,
    mock_check_glossary_owner,
    mock_check_mf_owner,
    mock_check_notification_recipient,
    mock_storage,
    field,
    perm_type,
    request,
    mocker,
    common_mocks,
):
    fid = request.node.callspec.id.split('-')[-1]
    perm, reason = EXPECTED_RESOLVERS[fid].get(perm_type)
    assert_that(field.resolver).is_not_none()
    msg = f'{fid} -> {getabsfile(unwrap(field.resolver))}:{getsourcelines(unwrap(field.resolver))[1]}'
    logging.info(msg)
    # Setup mock context
    username = 'ausername'
    groups = ['agroup']
    mock_storage.context = RequestContext(MagicMock(), username, groups, 'auserid')
    mock_feed_find_perm.return_value = perm
    mock_update_perm_name.return_value = perm
    mock_read_perm_name.return_value = perm
    mock_tenant_perm_name.return_value = perm

    iargs = {arg: MagicMock() for arg in signature(field.resolver).parameters.keys()}

    # run test specific setup if required
    globals().get(f'setup_{fid}', lambda *_a, **b: None)(**locals())  # nosemgrep

    try:
        field.resolver(**iargs)
    except:
        logging.info('expected exception', exc_info=True)

    if not perm:  # if no expected permission is defined, we expect the check to not be called
        locals()[f'mock_check_{perm_type}'].assert_not_called()  # nosemgrep
        pytest.skip(msg + f' Reason: {reason.value}')
    elif perm_type == 'resource':
        mock_check_resource.assert_any_call(
            session=ANY,
            resource_uri=ANY,
            username=username,
            groups=groups,
            permission_name=perm,
        )
    elif perm_type == 'tenant':
        mock_check_tenant.assert_any_call(
            session=ANY,
            username=username,
            groups=groups,
            tenant_name=ANY,
            permission_name=perm,
        )
    elif perm_type in ['tenant_admin', 'glossary_owner', 'mf_owner', 'notification_recipient']:
        locals()[f'mock_check_{perm_type}'].assert_called()  # nosemgrep
    else:
        raise ValueError(f'unknown permission type {perm_type}')
