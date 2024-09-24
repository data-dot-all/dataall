# TODO: This file will be replaced by using the SDK directly
def create_organization(client, name, group, tags=[]):
    query = {
        'operationName': 'CreateOrg',
        'variables': {
            'input': {
                'label': name,
                'SamlGroupName': group,
                'description': 'Created for integration testing',
                'tags': tags,
            }
        },
        'query': """mutation CreateOrg($input: NewOrganizationInput) {
                      createOrganization(input: $input) {
                        organizationUri
                        label
                        created
                        owner
                        SamlGroupName
                      }
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.createOrganization


def archive_organization(client, organizationUri):
    query = {
        'operationName': 'archiveOrganization',
        'variables': {'organizationUri': organizationUri},
        'query': """mutation archiveOrganization($organizationUri:String!){
                    archiveOrganization(organizationUri:$organizationUri)
                }
            """,
    }
    response = client.query(query=query)
    return response.data.archiveOrganization


def get_organization(client, organizationUri):
    query = {
        'operationName': 'GetOrg',
        'variables': {'organizationUri': organizationUri},
        'query': """query GetOrg($organizationUri:String!){
            getOrganization(organizationUri:$organizationUri){
                organizationUri
                label
                name
                owner
                SamlGroupName
                userRoleInOrganization
                stats{
                    environments
                    groups
                }
            }
        }
        """,
    }
    response = client.query(query=query)
    return response.data.getOrganization


def update_organization(client, organizationUri):
    query = {
        'operationName': 'UpdateOrg',
        'variables': {
            'organizationUri': organizationUri,
            'input': {'label': 'newlabel'},
        },
        'query': """ mutation UpdateOrg($organizationUri:String!,$input:ModifyOrganizationInput!){
                 updateOrganization(organizationUri:$organizationUri,input:$input){
                    label
                    owner
                    SamlGroupName
                }
            }
        """,
    }
    response = client.query(query=query)
    return response.data.updateOrganization


def invite_team_to_organization(client, organizationUri, group, permissions=None):
    query = {
        'operationName': 'inviteGroupToOrganization',
        'variables': {
            'input': {'organizationUri': organizationUri, 'groupUri': group, 'permissions': permissions or []}
        },
        'query': """mutation inviteGroupToOrganization($input:InviteGroupToOrganizationInput!){
            inviteGroupToOrganization(input:$input){
                organizationUri
            }
        }
            """,
    }
    response = client.query(query=query)
    return response.data.inviteGroupToOrganization


def remove_team_from_organization(client, organizationUri, group):
    query = {
        'operationName': 'removeGroupFromOrganization',
        'variables': {'organizationUri': organizationUri, 'groupUri': group},
        'query': """mutation removeGroupFromOrganization($organizationUri:String!,$groupUri:String!){
            removeGroupFromOrganization(organizationUri:$organizationUri,groupUri:$groupUri){
                organizationUri
            }
        }
            """,
    }
    response = client.query(query=query)
    return response.data.removeGroupFromOrganization


def update_tenant_permissions(client, group, permissions):
    query = {
        'operationName': 'updateGroupTenantPermissions',
        'variables': {'input': {'groupUri': group, 'permissions': permissions}},
        'query': """
        mutation updateGroupTenantPermissions($input: UpdateGroupTenantPermissionsInput!) {
          updateGroupTenantPermissions(input: $input)
          }
                """,
    }
    response = client.query(query=query)
    return response.data.updateGroupTenantPermissions


def list_organizations(client, term=''):
    query = {
        'operationName': 'ListOrg',
        'variables': {'filter': {'page': 1, 'pageSize': 10, 'term': term}},
        'query': """
                query ListOrg($filter:OrganizationFilter){
                    listOrganizations(filter:$filter){
                        count
                        nodes{
                            organizationUri
                            SamlGroupName
                        }
                    }
                }
                """,
    }
    response = client.query(query=query)
    return response.data.listOrganizations
