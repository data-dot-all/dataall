from dataall.core.permissions.db.tenant.tenant_policy_repositories import TenantPolicyRepository
from dataall.core.permissions.services.core_permissions import MANAGE_GROUPS, MANAGE_ORGANIZATIONS


def test_list_tenant_permissions(client, user, group, tenant):
    response = client.query(
        """
        query listTenantPermissions{
            listTenantPermissions{
                name
            }
        }
        """,
        username=user.username,
        groups=[group.name, TenantPolicyRepository.ADMIN_GROUP],
    )

    assert len(response.data.listTenantPermissions) >= 1

    response = client.query(
        """
        query listTenantPermissions{
            listTenantPermissions{
                name
            }
        }
        """,
        username=user.username,
        groups=[group.name],
    )
    assert 'UnauthorizedOperation' in response.errors[0].message

    response = client.query(
        """
        query listTenantGroups{
            listTenantGroups{
                nodes{
                    groupUri
                    tenantPermissions{
                        name
                    }
                }
            }
        }
        """,
        username=user.username,
        groups=[group.name, TenantPolicyRepository.ADMIN_GROUP],
    )

    assert group.name in [node.groupUri for node in response.data.listTenantGroups.nodes]


def test_update_permissions(client, user, group, tenant):
    response = client.query(
        """
        mutation updateGroupTenantPermissions($input:UpdateGroupTenantPermissionsInput!){
            updateGroupTenantPermissions(input:$input)
        }
        """,
        username='alice',
        input=dict(
            groupUri=group.name,
            permissions=[MANAGE_ORGANIZATIONS, MANAGE_GROUPS],
        ),
        groups=[group.name, TenantPolicyRepository.ADMIN_GROUP],
    )
    print(response)
    assert response.data.updateGroupTenantPermissions

    response = client.query(
        """
        query getGroup($groupUri:String!){
            getGroup(groupUri:$groupUri){
                tenantPermissions{
                 name
                }
            }
        }
        """,
        username=user.username,
        groups=[group.name, TenantPolicyRepository.ADMIN_GROUP],
        groupUri=group.name,
    )
    assert len(response.data.getGroup.tenantPermissions) == 2

    response = client.query(
        """
        mutation updateGroupTenantPermissions($input:UpdateGroupTenantPermissionsInput!){
            updateGroupTenantPermissions(input:$input)
        }
        """,
        username='alice',
        input=dict(
            groupUri=group.name,
            permissions=[MANAGE_ORGANIZATIONS, MANAGE_GROUPS],
        ),
        groups=[group.name, TenantPolicyRepository.ADMIN_GROUP],
    )
    print(response)
    assert response.data.updateGroupTenantPermissions
