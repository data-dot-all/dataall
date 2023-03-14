import pytest

from dataall.db import models


@pytest.fixture(scope='module')
def org1(db, org, tenant, user, group) -> models.Organization:
    org = org('testorg', user.userName, group.name)
    yield org


@pytest.fixture(scope='module')
def env1(
    db, org1: models.Organization, user, group, module_mocker, env
) -> models.Environment:
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def dataset1(db, env1, org1, group, user, dataset, module_mocker) -> models.Dataset:
    with db.scoped_session() as session:
        module_mocker.patch(
            'dataall.api.Objects.Dataset.resolvers.check_dataset_account', return_value=True
        )
        yield dataset(
            org=org1, env=env1, name='dataset1', owner=user.userName, group=group.name
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


def test_count_votes(client, dataset1, dashboard):
    response = count_votes_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 0
    response = count_votes_query(
        client, dashboard.dashboardUri, 'dashboard', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 0


def count_votes_query(client, target_uri, target_type, group):
    response = client.query(
        """
        query countUpVotes($targetUri:String!, $targetType:String!){
            countUpVotes(targetUri:$targetUri, targetType:$targetType)
        }
        """,
        targetUri=target_uri,
        targetType=target_type,
        username='alice',
        groups=[group],
    )
    return response


def get_vote_query(client, target_uri, target_type, group):
    response = client.query(
        """
        query getVote($targetUri:String!, $targetType:String!){
            getVote(targetUri:$targetUri, targetType:$targetType){
             upvote
            }
        }
        """,
        targetUri=target_uri,
        targetType=target_type,
        username='alice',
        groups=[group],
    )
    return response


def test_upvote(patch_es, client, dataset1, module_mocker, dashboard):
    module_mocker.patch('dataall.api.Objects.Vote.resolvers.reindex', return_value={})
    response = upvote_mutation(
        client, dataset1.datasetUri, 'dataset', True, dataset1.SamlAdminGroupName
    )
    assert response.data.upVote.upvote
    response = count_votes_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 1
    response = get_vote_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert response.data.getVote.upvote

    response = upvote_mutation(
        client, dashboard.dashboardUri, 'dashboard', True, dataset1.SamlAdminGroupName
    )
    assert response.data.upVote.upvote
    response = count_votes_query(
        client, dashboard.dashboardUri, 'dashboard', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 1
    response = get_vote_query(
        client, dashboard.dashboardUri, 'dashboard', dataset1.SamlAdminGroupName
    )
    assert response.data.getVote.upvote

    response = upvote_mutation(
        client, dataset1.datasetUri, 'dataset', False, dataset1.SamlAdminGroupName
    )
    assert not response.data.upVote.upvote
    response = upvote_mutation(
        client, dashboard.dashboardUri, 'dashboard', False, dataset1.SamlAdminGroupName
    )

    assert not response.data.upVote.upvote
    response = get_vote_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert not response.data.getVote.upvote
    response = get_vote_query(
        client, dashboard.dashboardUri, 'dashboard', dataset1.SamlAdminGroupName
    )
    assert not response.data.getVote.upvote

    response = count_votes_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 0
    response = count_votes_query(
        client, dashboard.dashboardUri, 'dashboard', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 0


def upvote_mutation(client, target_uri, target_type, upvote, group):
    response = client.query(
        """
        mutation upVote($input:VoteInput!){
            upVote(input:$input){
                voteUri
                targetUri
                targetType
                upvote
            }
        }
        """,
        input=dict(
            targetUri=target_uri,
            targetType=target_type,
            upvote=upvote,
        ),
        username='alice',
        groups=[group],
    )
    return response
