# TODO: This file will be replaced by using the SDK directly


def list_environment_redshift_connections(client, term='', environment_uri=None, group_uri=None, connection_type=None):
    query = {
        'operationName': 'listEnvironmentRedshiftConnections',
        'variables': {
            'filter': {
                'term': term,
                'environmentUri': environment_uri,
                'groupUri': group_uri,
                'connectionType': connection_type,
            }
        },
        'query': """
            query listEnvironmentRedshiftConnections($filter: ConnectionFilter) {
              listEnvironmentRedshiftConnections(filter: $filter) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                  name
                  connectionUri
                  SamlGroupName
                  redshiftType
                  clusterId
                  nameSpaceId
                  workgroup
                  database
                  redshiftUser
                  secretArn
                  connectionType
                }
              }
            }
                        """,
    }
    response = client.query(query=query)
    return response.data.listEnvironmentRedshiftConnections


def list_redshift_connection_schemas(client, connection_uri):
    query = {
        'operationName': 'listRedshiftConnectionSchemas',
        'variables': {'connectionUri': connection_uri},
        'query': """
                    query listRedshiftConnectionSchemas($connectionUri: String!) {
                      listRedshiftConnectionSchemas(connectionUri: $connectionUri)
                    }
                """,
    }
    response = client.query(query=query)
    return response.data.listRedshiftConnectionSchemas


def list_redshift_schema_tables(client, connection_uri, schema):
    query = {
        'operationName': 'listRedshiftSchemaTables',
        'variables': {'connectionUri': connection_uri, 'schema': schema},
        'query': """
                query listRedshiftSchemaTables($connectionUri: String!, $schema: String!) {
                  listRedshiftSchemaTables(connectionUri: $connectionUri, schema: $schema) {
                    name
                    type
                  }
                }
            """,
    }
    response = client.query(query=query)
    return response.data.listRedshiftSchemaTables


def list_redshift_connection_group_permissions(client, connection_uri, filter={}):
    query = {
        'operationName': 'listConnectionGroupPermissions',
        'variables': {'connectionUri': connection_uri, 'filter': filter},
        'query': """
            query listConnectionGroupPermissions(
                  $filter: GroupFilter
                  $connectionUri: String!
                ) {
                  listConnectionGroupPermissions(
                    connectionUri: $connectionUri
                    filter: $filter
                  ) {
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes {
                      groupUri
                      permissions {
                        name
                        description
                      }
                    }
                  }
                }
                """,
    }
    response = client.query(query=query)
    return response.data.listConnectionGroupPermissions


def list_redshift_connection_group_no_permissions(client, connection_uri, term=''):
    query = {
        'operationName': 'listConnectionGroupNoPermissions',
        'variables': {'connectionUri': connection_uri, 'filter': {'term': term}},
        'query': """
            query listConnectionGroupNoPermissions(
              $filter: GroupFilter
              $connectionUri: String!
            ) {
              listConnectionGroupNoPermissions(
                connectionUri: $connectionUri
                filter: $filter
              )
            }
        """,
    }
    response = client.query(query=query)
    return response.data.listConnectionGroupNoPermissions


def create_redshift_connection(
    client,
    connection_name,
    environment_uri,
    group_uri,
    redshift_type,
    database,
    connection_type,
    cluster_id=None,
    namespace_id=None,
    workgroup=None,
    redshift_user=None,
    secret_arn=None,
):
    query = {
        'operationName': 'createRedshiftConnection',
        'variables': {
            'input': {
                'connectionName': connection_name,
                'connectionType': connection_type,
                'environmentUri': environment_uri,
                'SamlGroupName': group_uri,
                'redshiftType': redshift_type,
                'clusterId': cluster_id,
                'nameSpaceId': namespace_id,
                'workgroup': workgroup,
                'database': database,
                'redshiftUser': redshift_user,
                'secretArn': secret_arn,
            }
        },
        'query': """
            mutation createRedshiftConnection($input: CreateRedshiftConnectionInput) {
              createRedshiftConnection(input: $input) {
                connectionUri
                connectionType
                redshiftType
                name
                nameSpaceId
              }
            }
        """,
    }
    response = client.query(query=query)
    return response.data.createRedshiftConnection


def delete_redshift_connection(client, connection_uri):
    query = {
        'operationName': 'deleteRedshiftConnection',
        'variables': {'connectionUri': connection_uri},
        'query': """
            mutation deleteRedshiftConnection($connectionUri: String!) {
              deleteRedshiftConnection(connectionUri: $connectionUri)
            }
        """,
    }
    response = client.query(query=query)
    return response.data.deleteRedshiftConnection


def add_redshift_connection_group_permissions(client, connection_uri, group_uri, permissions):
    query = {
        'operationName': 'addConnectionGroupPermission',
        'variables': {'connectionUri': connection_uri, 'groupUri': group_uri, 'permissions': permissions},
        'query': """
                mutation addConnectionGroupPermission(
                  $connectionUri: String!
                  $groupUri: String!
                  $permissions: [String]!
                ) {
                  addConnectionGroupPermission(
                    connectionUri: $connectionUri
                    groupUri: $groupUri
                    permissions: $permissions
                  )
                }
        """,
    }
    response = client.query(query=query)
    return response.data.addConnectionGroupPermission


def delete_redshift_connection_group_permissions(client, connection_uri, group_uri):
    query = {
        'operationName': 'deleteConnectionGroupPermission',
        'variables': {'connectionUri': connection_uri, 'groupUri': group_uri},
        'query': """
            mutation deleteConnectionGroupPermission(
              $connectionUri: String!
              $groupUri: String!
            ) {
              deleteConnectionGroupPermission(
                connectionUri: $connectionUri
                groupUri: $groupUri
              )
            }
        """,
    }
    response = client.query(query=query)
    return response.data.deleteConnectionGroupPermission
