# TODO: This file will be replaced by using the SDK directly

# # IF MONITORING ON (TODO)
# createQuicksightDataSourceSet (TODO)


def import_dashboard(client, input):
    query = {
        'operationName': 'importDashboard',
        'variables': {'input': input},
        'query': """
                  mutation importDashboard($input: ImportDashboardInput!) {
                    importDashboard(input: $input) {
                      dashboardUri
                      name
                      label
                      DashboardId
                      created
                    }
                  }
                """,
    }
    response = client.query(query=query)
    return response.data.importDashboard


def update_dashboard(client, input):
    query = {
        'operationName': 'updateDashboard',
        'variables': {'input': input},
        'query': """
                  mutation updateDashboard($input: UpdateDashboardInput!) {
                    updateDashboard(input: $input) {
                      dashboardUri
                      name
                      label
                      created
                    }
                  }
                """,
    }
    response = client.query(query=query)
    return response.data.importDashboard


def delete_dashboard(client, dashboardUri):
    query = {
        'operationName': 'deleteDashboard',
        'variables': {'dashboardUri': dashboardUri},
        'query': """
                  mutation deleteDashboard($dashboardUri: String!)  {
                    deleteDashboard(dashboardUri: $dashboardUri)
                  }
                """,
    }
    response = client.query(query=query)
    return response.data.deleteDashboard


def request_dashboard_share(client, dashboardUri, principalId):
    query = {
        'operationName': 'requestDashboardShare',
        'variables': {'dashboardUri': dashboardUri, 'principalId': principalId},
        'query': """
                  mutation requestDashboardShare($dashboardUri: String!,$principalId: String!) {
                    requestDashboardShare(dashboardUri: $dashboardUri,principalId: $principalId) {
                      shareUri
                      status
                    }
                  }
                """,
    }
    response = client.query(query=query)
    return response.data.requestDashboardShare


def approve_dashboard_share(client, shareUri):
    query = {
        'operationName': 'approveDashboardShare',
        'variables': {'shareUri': shareUri},
        'query': """
                  mutation approveDashboardShare($shareUri: String!) {
                    approveDashboardShare(shareUri: $shareUri) {
                      shareUri
                      status
                    }
                  }
                """,
    }
    response = client.query(query=query)
    return response.data.approveDashboardShare


def reject_dashboard_share(client, shareUri):
    query = {
        'operationName': 'rejectDashboardShare',
        'variables': {'shareUri': shareUri},
        'query': """
                  mutation rejectDashboardShare($shareUri: String!) {
                    rejectDashboardShare(shareUri: $shareUri) {
                      shareUri
                      status
                    }
                  }
                """,
    }
    response = client.query(query=query)
    return response.data.rejectDashboardShare
