from tests.modules.vote.test_vote import upvote_mutation, count_votes_query, get_vote_query


def test_dashboard_count_votes(client, dashboard, env_fixture):
    response = count_votes_query(client, dashboard.dashboardUri, 'dashboard', env_fixture.SamlGroupName)
    assert response.data.countUpVotes == 0


def test_dashboard_upvote(patch_es, client, env_fixture, dashboard):
    response = upvote_mutation(client, dashboard.dashboardUri, 'dashboard', True, env_fixture.SamlGroupName)
    assert response.data.upVote.upvote
    response = count_votes_query(client, dashboard.dashboardUri, 'dashboard', env_fixture.SamlGroupName)
    assert response.data.countUpVotes == 1
    response = get_vote_query(client, dashboard.dashboardUri, 'dashboard', env_fixture.SamlGroupName)
    assert response.data.getVote.upvote

    response = upvote_mutation(client, dashboard.dashboardUri, 'dashboard', False, env_fixture.SamlGroupName)

    assert not response.data.upVote.upvote

    response = get_vote_query(client, dashboard.dashboardUri, 'dashboard', env_fixture.SamlGroupName)
    assert not response.data.getVote.upvote

    response = count_votes_query(client, dashboard.dashboardUri, 'dashboard', env_fixture.SamlGroupName)
    assert response.data.countUpVotes == 0
