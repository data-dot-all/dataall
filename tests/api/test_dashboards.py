import typing
import pytest

import dataall
from dataall.modules.datasets_base.db.models import Dataset


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module')
def dataset1(
    org1: dataall.db.models.Organization,
    env1: dataall.db.models.Environment,
    dataset: typing.Callable,
) -> Dataset:
    yield dataset(
        org=org1, env=env1, name='dataset1', owner=env1.owner, group='dataset1admins'
    )


@pytest.fixture(scope='module')
def dashboard(client, env1, org1, group, module_mocker, patch_es):
    module_mocker.patch(
        'dataall.aws.handlers.quicksight.Quicksight.can_import_dashboard',
        return_value=True,
    )
    response = client.query(
        """
            mutation importDashboard(
                $input:ImportDashboardInput,
            ){
                importDashboard(input:$input){
                    dashboardUri
                    name
                    label
                    DashboardId
                    created
                    owner
                    SamlGroupName
                    upvotes
                    userRoleForDashboard
                }
            }
        """,
        input={
            'dashboardId': f'1234',
            'label': f'1234',
            'environmentUri': env1.environmentUri,
            'SamlGroupName': group.name,
            'terms': ['term'],
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.importDashboard.owner == 'alice'
    assert response.data.importDashboard.SamlGroupName == group.name
    yield response.data.importDashboard


def test_update_dashboard(
    client, env1, org1, group, module_mocker, patch_es, dashboard
):
    module_mocker.patch(
        'dataall.aws.handlers.quicksight.Quicksight.can_import_dashboard',
        return_value=True,
    )
    response = client.query(
        """
            mutation updateDashboard(
                $input:UpdateDashboardInput,
            ){
                updateDashboard(input:$input){
                    dashboardUri
                    name
                    label
                    DashboardId
                    created
                    owner
                    SamlGroupName
                }
            }
        """,
        input={
            'dashboardUri': dashboard.dashboardUri,
            'label': f'1234',
            'terms': ['term2'],
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.updateDashboard.owner == 'alice'
    assert response.data.updateDashboard.SamlGroupName == group.name


def test_list_dashboards(client, env1, db, org1, dashboard):
    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                }
            }
        }
        """,
        filter={},
        username='alice',
    )
    assert len(response.data.searchDashboards['nodes']) == 1


def test_nopermissions_list_dashboards(client, env1, db, org1, dashboard):
    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                }
            }
        }
        """,
        filter={},
        username='bob',
    )
    assert len(response.data.searchDashboards['nodes']) == 0


def test_get_dashboard(client, env1, db, org1, dashboard, group):
    response = client.query(
        """
        query GetDashboard($dashboardUri:String!){
                getDashboard(dashboardUri:$dashboardUri){
                    dashboardUri
                    name
                    owner
                    SamlGroupName
                    description
                    label
                    created
                    tags
                    environment{
                        label
                        region
                    }
                    organization{
                        organizationUri
                        label
                        name
                    }
                }
            }
        """,
        dashboardUri=dashboard.dashboardUri,
        username='alice',
        groups=[group.name],
    )
    assert response.data.getDashboard.owner == 'alice'
    assert response.data.getDashboard.SamlGroupName == group.name


def test_request_dashboard_share(
    client,
    env1,
    db,
    org1,
    user,
    group,
    module_mocker,
    dashboard,
    patch_es,
    group2,
    user2,
):
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation requestDashboardShare($dashboardUri:String!, $principalId:String!){
            requestDashboardShare(dashboardUri:$dashboardUri, principalId:$principalId){
                shareUri
                status
            }
        }
        """,
        dashboardUri=dashboard.dashboardUri,
        principalId=group2.name,
        username=user2.userName,
        groups=[group2.name],
    )
    share = response.data.requestDashboardShare
    assert share.shareUri
    assert share.status == 'REQUESTED'

    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                    userRoleForDashboard
                }
            }
        }
        """,
        filter={},
        username=user2.userName,
        groups=[group2.name],
    )
    assert len(response.data.searchDashboards['nodes']) == 0

    response = client.query(
        """
        mutation approveDashboardShare($shareUri:String!){
            approveDashboardShare(shareUri:$shareUri){
                shareUri
                status
            }
        }
        """,
        shareUri=share.shareUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.approveDashboardShare.status == 'APPROVED'

    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                    userRoleForDashboard
                }
            }
        }
        """,
        filter={},
        username=user2.userName,
        groups=[group2.name],
    )
    assert len(response.data.searchDashboards['nodes']) == 1

    response = client.query(
        """
        query listDashboardShares($dashboardUri:String!,$filter:DashboardShareFilter!){
            listDashboardShares(dashboardUri:$dashboardUri,filter:$filter){
                count
                nodes{
                    dashboardUri
                    shareUri
                }
            }
        }
        """,
        filter={},
        dashboardUri=dashboard.dashboardUri,
        username=user.userName,
        groups=[group.name],
    )
    assert len(response.data.listDashboardShares['nodes']) == 1

    response = client.query(
        """
        query GetDashboard($dashboardUri:String!){
                getDashboard(dashboardUri:$dashboardUri){
                    dashboardUri
                    name
                    owner
                    SamlGroupName
                    description
                    label
                    created
                    tags
                    environment{
                        label
                        region
                    }
                    organization{
                        organizationUri
                        label
                        name
                    }
                }
            }
        """,
        dashboardUri=dashboard.dashboardUri,
        username=user2.userName,
        groups=[group2.name],
    )
    assert response.data.getDashboard.owner == 'alice'
    assert response.data.getDashboard.SamlGroupName == group.name

    response = client.query(
        """
        mutation rejectDashboardShare($shareUri:String!){
            rejectDashboardShare(shareUri:$shareUri){
                shareUri
                status
            }
        }
        """,
        shareUri=share.shareUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.rejectDashboardShare.status == 'REJECTED'

    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                    userRoleForDashboard
                }
            }
        }
        """,
        filter={},
        username=user2.userName,
        groups=[group2.name],
    )
    assert len(response.data.searchDashboards['nodes']) == 0

    response = client.query(
        """
        mutation shareDashboard($dashboardUri:String!, $principalId:String!){
            shareDashboard(dashboardUri:$dashboardUri, principalId:$principalId){
                shareUri
                status
            }
        }
        """,
        dashboardUri=dashboard.dashboardUri,
        principalId=group2.name,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.shareDashboard.shareUri

    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                    userRoleForDashboard
                }
            }
        }
        """,
        filter={},
        username=user2.userName,
        groups=[group2.name],
    )
    assert len(response.data.searchDashboards['nodes']) == 1


def test_delete_dashboard(
    client, env1, db, org1, user, group, module_mocker, dashboard, patch_es
):
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation deleteDashboard($dashboardUri:String!){
            deleteDashboard(dashboardUri:$dashboardUri)
        }
        """,
        dashboardUri=dashboard.dashboardUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.deleteDashboard
    response = client.query(
        """
        query searchDashboards($filter:DashboardFilter!){
            searchDashboards(filter:$filter){
                count
                nodes{
                    dashboardUri
                }
            }
        }
        """,
        filter={},
        username='alice',
    )
    assert len(response.data.searchDashboards['nodes']) == 0
