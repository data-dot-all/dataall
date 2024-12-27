# TODO: This file will be replaced by using the SDK directly
def update_group_tenant_permissions(client, group_uri, permissions=[]):
    query = {
        'operationName': 'updateGroupTenantPermissions',
        'variables': {
            'input': {
                'groupUri': group_uri,
                'permissions': permissions,
            }
        },
        'query': """    
                mutation updateGroupTenantPermissions(
                  $input: UpdateGroupTenantPermissionsInput!
                ) {
                  updateGroupTenantPermissions(input: $input)
                }
                """,
    }
    response = client.query(query=query)
    return response.data.updateGroupTenantPermissions


def list_tenant_permissions(client):
    query = {
        'operationName': 'listTenantPermissions',
        'variables': {},
        'query': """    
                query listTenantPermissions {
                  listTenantPermissions {
                    name
                    description
                  }
                }
                """,
    }
    response = client.query(query=query)
    return response.data.listTenantPermissions


def list_tenant_groups(client, term=''):
    query = {
        'operationName': 'listTenantGroups',
        'variables': {'filter': {'term': term}},
        'query': """    
            query listTenantGroups($filter: GroupFilter) {
              listTenantGroups(filter: $filter) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                  groupUri
                  tenantPermissions {
                    name
                    description
                  }
                }
              }
            }
            """,
    }
    response = client.query(query=query)
    return response.data.listTenantGroups
