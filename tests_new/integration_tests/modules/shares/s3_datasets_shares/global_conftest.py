import pytest

from tests_new.integration_tests.aws_clients.iam import IAMClient
from tests_new.integration_tests.core.environment.queries import (
    add_consumption_role,
    remove_consumption_role,
    list_environment_consumption_roles,
)
from tests_new.integration_tests.modules.shares.queries import (
    create_share_object,
    delete_share_object,
    get_share_object,
    revoke_share_items,
    submit_share_object,
    approve_share_object,
    add_share_item,
)
from tests_new.integration_tests.modules.shares.utils import check_share_ready

test_session_cons_role_name = 'dataall-test-ShareTestConsumptionRole'
test_persistent_cons_role_name = 'dataall-test-PersistentConsumptionRole'


def revoke_all_possible(client, shareUri):
    share = get_share_object(client, shareUri, {'isShared': True})
    statuses_can_delete = [
        'PendingApproval',
        'Revoke_Succeeded',
        'Share_Failed',
        'Share_Rejected',
    ]

    shareItemUris = [item.shareItemUri for item in share['items'].nodes if item.status not in statuses_can_delete]
    if shareItemUris:
        revoke_share_items(client, shareUri, shareItemUris)


def clean_up_share(client, shareUri):
    check_share_ready(client, shareUri)
    revoke_all_possible(client, shareUri)
    check_share_ready(client, shareUri)
    delete_share_object(client, shareUri)


def create_consumption_role(client, group, environment, environment_client, iam_role_name, cons_role_name):
    iam_client = IAMClient(session=environment_client, region=environment['region'])
    role = iam_client.get_consumption_role(
        environment.AwsAccountId,
        iam_role_name,
        f'dataall-integration-tests-role-{environment.region}',
    )
    return add_consumption_role(
        client,
        environment.environmentUri,
        group,
        cons_role_name,
        role['Role']['Arn'],
    )


# --------------SESSION PARAM FIXTURES----------------------------


@pytest.fixture(scope='session')
def session_consumption_role_1(client5, group5, session_cross_acc_env_1, session_cross_acc_env_1_aws_client):
    consumption_role = create_consumption_role(
        client5,
        group5,
        session_cross_acc_env_1,
        session_cross_acc_env_1_aws_client,
        test_session_cons_role_name,
        'SessionConsRole1',
    )
    yield consumption_role
    remove_consumption_role(client5, session_cross_acc_env_1.environmentUri, consumption_role.consumptionRoleUri)
    iam_client = IAMClient(session=session_cross_acc_env_1_aws_client, region=session_cross_acc_env_1['region'])
    iam_client.delete_consumption_role(test_session_cons_role_name)


@pytest.fixture(scope='session')
def session_share_1(
    client5,
    client1,
    session_cross_acc_env_1,
    session_s3_dataset1,
    session_s3_dataset1_tables,
    session_s3_dataset1_folders,
    group5,
):
    share1 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=group5,
        principalType='Group',
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share1 = get_share_object(client5, share1.shareUri)
    yield share1
    clean_up_share(client5, share1.shareUri)


@pytest.fixture(scope='session')
def session_share_2(
    client5,
    client1,
    session_cross_acc_env_1,
    session_imported_sse_s3_dataset1,
    session_imported_sse_s3_dataset1_tables,
    session_imported_sse_s3_dataset1_folders,
    group5,
):
    share2 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_imported_sse_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=group5,
        principalType='Group',
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share2 = get_share_object(client5, share2.shareUri)
    yield share2

    clean_up_share(client5, share2.shareUri)


@pytest.fixture(scope='session')
def session_share_consrole_1(
    client5,
    client1,
    session_cross_acc_env_1,
    session_s3_dataset1,
    session_s3_dataset1_tables,
    session_s3_dataset1_folders,
    group5,
    session_consumption_role_1,
):
    share1cr = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=session_consumption_role_1.consumptionRoleUri,
        principalType='ConsumptionRole',
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share1cr = get_share_object(client5, share1cr.shareUri)
    yield share1cr
    clean_up_share(client5, share1cr.shareUri)


@pytest.fixture(scope='session')
def session_share_consrole_2(
    client5,
    client1,
    session_cross_acc_env_1,
    session_imported_sse_s3_dataset1,
    session_imported_sse_s3_dataset1_tables,
    session_imported_sse_s3_dataset1_folders,
    group5,
    session_consumption_role_1,
):
    share2cr = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_imported_sse_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=session_consumption_role_1.consumptionRoleUri,
        principalType='ConsumptionRole',
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share2cr = get_share_object(client5, share2cr.shareUri)
    yield share2cr

    clean_up_share(client5, share2cr.shareUri)


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def principal1(request, group5, session_consumption_role_1):
    if request.param == 'Group':
        yield group5, request.param
    else:
        yield session_consumption_role_1.consumptionRoleUri, request.param


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def share_params_main(request, session_share_1, session_share_consrole_1, session_s3_dataset1):
    if request.param == 'Group':
        yield session_share_1, session_s3_dataset1
    else:
        yield session_share_consrole_1, session_s3_dataset1


@pytest.fixture(params=[(False, 'Group'), (True, 'Group'), (False, 'ConsumptionRole'), (True, 'ConsumptionRole')])
def share_params_all(
    request,
    session_share_1,
    session_share_consrole_1,
    session_s3_dataset1,
    session_share_2,
    session_share_consrole_2,
    session_imported_sse_s3_dataset1,
):
    autoapproval, principal_type = request.param
    if autoapproval:
        if principal_type == 'Group':
            yield session_share_2, session_imported_sse_s3_dataset1
        else:
            yield session_share_consrole_2, session_imported_sse_s3_dataset1
    else:
        if principal_type == 'Group':
            yield session_share_1, session_s3_dataset1
        else:
            yield session_share_consrole_1, session_s3_dataset1


# --------------PERSISTENT FIXTURES----------------------------


@pytest.fixture(scope='session')
def persistent_consumption_role_1(client5, group5, persistent_cross_acc_env_1, persistent_cross_acc_env_1_aws_client):
    consumption_roles_result = list_environment_consumption_roles(
        client5,
        persistent_cross_acc_env_1.environmentUri,
        {'term': 'PersistentConsRole1'},
    )

    if consumption_roles_result.count == 0:
        consumption_role = create_consumption_role(
            client5,
            group5,
            persistent_cross_acc_env_1,
            persistent_cross_acc_env_1_aws_client,
            test_persistent_cons_role_name,
            'PersistentConsRole1',
        )
        yield consumption_role
    else:
        yield consumption_roles_result.nodes[0]


@pytest.fixture(scope='session')
def persistent_group_share_1(
    client5,
    client1,
    persistent_env1,
    persistent_cross_acc_env_1,
    updated_persistent_s3_dataset1,
    group5,
):
    share1 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': updated_persistent_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=group5,
        principalType='Group',
        requestPurpose='create persistent share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share1 = get_share_object(client5, share1.shareUri)

    if share1.status == 'Draft':
        items = share1['items'].nodes
        for item in items:
            add_share_item(client5, share1.shareUri, item.itemUri, item.itemType)
        submit_share_object(client5, share1.shareUri)
        approve_share_object(client1, share1.shareUri)
    check_share_ready(client5, share1.shareUri)
    yield get_share_object(client5, share1.shareUri)


@pytest.fixture(scope='session')
def persistent_role_share_1(
    client5,
    client1,
    persistent_env1,
    persistent_cross_acc_env_1,
    updated_persistent_s3_dataset1,
    group5,
    persistent_consumption_role_1,
):
    share1 = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': updated_persistent_s3_dataset1.datasetUri},
        environmentUri=persistent_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=persistent_consumption_role_1.consumptionRoleUri,
        principalType='ConsumptionRole',
        requestPurpose='create persistent share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share1 = get_share_object(client5, share1.shareUri)

    if share1.status == 'Draft':
        items = share1['items'].nodes
        for item in items:
            add_share_item(client5, share1.shareUri, item.itemUri, item.itemType)
        submit_share_object(client5, share1.shareUri)
        approve_share_object(client1, share1.shareUri)
    check_share_ready(client5, share1.shareUri)
    yield get_share_object(client5, share1.shareUri)


@pytest.fixture(params=['Group', 'ConsumptionRole'])
def persistent_share_params_main(request, persistent_role_share_1, persistent_group_share_1):
    if request.param == 'Group':
        yield persistent_group_share_1
    else:
        yield persistent_role_share_1
