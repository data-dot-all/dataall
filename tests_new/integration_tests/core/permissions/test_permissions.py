from assertpy import assert_that

from integration_tests.core.permissions.queries import (
    update_group_tenant_permissions,
    list_tenant_permissions,
    list_tenant_groups,
)
from integration_tests.errors import GqlError


def test_list_tenant_permissions(clientTenant):
    response = list_tenant_permissions(clientTenant)
    assert_that(response).is_not_empty()
    assert_that(len(response)).is_greater_than_or_equal_to(3)
    assert_that(response).does_not_contain([None, '', False])
    assert_that([p.name for p in response]).does_not_contain([None, '', False])


def test_list_tenant_permissions_unauthorized(client1):
    assert_that(list_tenant_permissions).raises(GqlError).when_called_with(client1).contains(
        'UnauthorizedOperation', 'LIST_TENANT_TEAM_PERMISSIONS'
    )


def test_list_tenant_groups(clientTenant):
    response = list_tenant_groups(clientTenant)
    assert_that(response.count).is_greater_than_or_equal_to(4)
    assert_that(response.nodes).is_not_empty()
    assert_that(response.nodes[0]).contains_key('tenantPermissions')
    ## Testing admin group DAAdministrators exists
    admin_group = next(group for group in response.nodes if group.groupUri == 'DHAdmins')
    assert_that(admin_group).contains_key('tenantPermissions')


def test_list_tenant_groups_unauthorized(client1):
    assert_that(list_tenant_groups).raises(GqlError).when_called_with(client1).contains(
        'UnauthorizedOperation', 'LIST_TENANT_TEAMS'
    )


def test_update_group_tenant_permissions(clientTenant, group1):
    # get group with permissions
    response = list_tenant_groups(clientTenant, term=group1)
    assert_that(response.count).is_equal_to(1)
    assert_that(len(response.nodes[0].tenantPermissions)).is_greater_than_or_equal_to(1)
    group1_perms = [p.name for p in response.nodes[0].tenantPermissions]
    # update permissions
    response = update_group_tenant_permissions(clientTenant, group1, group1_perms[:-1])
    assert_that(response).is_true()
    # check permissions were updated
    response = list_tenant_groups(clientTenant, term=group1)
    assert_that(response.count).is_equal_to(1)
    group1_p_updated = response.nodes[0]
    assert_that(len(group1_p_updated.tenantPermissions)).is_equal_to(len(group1_perms) - 1)
    assert_that(group1_p_updated.tenantPermissions).does_not_contain(group1_perms[-1])
    # update permissions back to initial state
    update_group_tenant_permissions(clientTenant, group1, group1_perms)
