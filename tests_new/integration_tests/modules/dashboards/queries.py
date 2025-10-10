# TODO: This file will be replaced by using the SDK directly


# # IF MONITORING ON (TODO)
# getMonitoringDashboardId
# getMonitoringVpcConnectionId
# getPlatformReaderSession


def search_dashboards(client, filter):
    query = {
        'operationName': 'searchDashboards',
        'variables': {'filter': filter},
        'query': """
            query searchDashboards($filter: DashboardFilter) {
              searchDashboards(filter: $filter) {
                count
                page
                pages
                hasNext
                hasPrevious
                nodes {
                  dashboardUri
                  name
                  owner
                  SamlGroupName
                  description
                  label
                  created
                  tags
                  userRoleForDashboard
                  upvotes
                  restricted {
                    region
                    AwsAccountId
                  }
                  environment {
                    environmentUri
                    label
                    organization {
                      organizationUri
                      label
                    }
                  }
                }
              }
            }
        """,
    }
    response = client.query(query=query)
    return response.data.searchDashboards


def get_dashboard(client, dashboardUri):
    query = {
        'operationName': 'GetDashboard',
        'variables': {'dashboardUri': dashboardUri},
        'query': """
            query GetDashboard($dashboardUri: String!) {
              getDashboard(dashboardUri: $dashboardUri) {
                dashboardUri
                name
                owner
                SamlGroupName
                description
                label
                created
                tags
                userRoleForDashboard
                restricted {
                    region
                    AwsAccountId
                }
                environment {
                  environmentUri
                  label
                  organization {
                    organizationUri
                    label
                  }
                }
                terms {
                  count
                  nodes {
                    nodeUri
                    path
                    label
                  }
                }
              }
            }
        """,
    }
    response = client.query(query=query)
    return response.data.getDashboard


def list_dashboard_shares(client, dashboardUri, filter):
    query = {
        'operationName': 'listDashboardShares',
        'variables': {'dashboardUri': dashboardUri, 'filter': filter},
        'query': """
            query listDashboardShares($dashboardUri: String!,$filter: DashboardShareFilter!) {
              listDashboardShares(dashboardUri: $dashboardUri, filter: $filter) {
                count
                nodes {
                  dashboardUri
                  shareUri
                  SamlGroupName
                  owner
                  created
                  status
                }
              }
            }
        """,
    }
    response = client.query(query=query)
    return response.data.listDashboardShares


def get_author_session(client, environmentUri):
    query = {
        'operationName': 'GetAuthorSession',
        'variables': {'environmentUri': environmentUri},
        'query': """
            query GetAuthorSession($environmentUri: String!) {
              getAuthorSession(environmentUri: $environmentUri)
            }
        """,
    }
    response = client.query(query=query)
    return response.data.getAuthorSession


def get_reader_session(client, dashboardUri):
    query = {
        'operationName': 'GetReaderSession',
        'variables': {
            'dashboardUri': dashboardUri,
        },
        'query': """
            query GetReaderSession($dashboardUri: String!) {
              getReaderSession(dashboardUri: $dashboardUri)
            }
        """,
    }
    response = client.query(query=query)
    return response.data.getReaderSession
