from tests.api.test_vote import upvote_mutation, count_votes_query, get_vote_query


def test_dashboard_count_votes(client, dashboard, env1):
    response = count_votes_query(
        client, dashboard.dashboardUri, 'dashboard', env1.SamlGroupName
    )
    assert response.data.countUpVotes == 0


def test_dashboard_upvote(patch_es, client, env1, dashboard):

    response = upvote_mutation(
        client, dashboard.dashboardUri, 'dashboard', True, env1.SamlGroupName
    )
    assert response.data.upVote.upvote
    response = count_votes_query(
        client, dashboard.dashboardUri, 'dashboard', env1.SamlGroupName
    )
    assert response.data.countUpVotes == 1
    response = get_vote_query(
        client, dashboard.dashboardUri, 'dashboard', env1.SamlGroupName
    )
    assert response.data.getVote.upvote

    response = upvote_mutation(
        client, dashboard.dashboardUri, 'dashboard', False, env1.SamlGroupName
    )

    assert not response.data.upVote.upvote

    response = get_vote_query(
        client, dashboard.dashboardUri, 'dashboard', env1.SamlGroupName
    )
    assert not response.data.getVote.upvote

    response = count_votes_query(
        client, dashboard.dashboardUri, 'dashboard', env1.SamlGroupName
    )
    assert response.data.countUpVotes == 0