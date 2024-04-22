from tests.modules.vote.test_vote import *


def test_count_votes(client, dataset_fixture):
    response = count_votes_query(client, dataset_fixture.datasetUri, 'dataset', dataset_fixture.SamlAdminGroupName)
    assert response.data.countUpVotes == 0


def test_upvote(patch_es, client, dataset_fixture):
    response = upvote_mutation(client, dataset_fixture.datasetUri, 'dataset', True, dataset_fixture.SamlAdminGroupName)
    assert response.data.upVote.upvote
    response = count_votes_query(client, dataset_fixture.datasetUri, 'dataset', dataset_fixture.SamlAdminGroupName)
    assert response.data.countUpVotes == 1
    response = get_vote_query(client, dataset_fixture.datasetUri, 'dataset', dataset_fixture.SamlAdminGroupName)
    assert response.data.getVote.upvote

    response = upvote_mutation(client, dataset_fixture.datasetUri, 'dataset', False, dataset_fixture.SamlAdminGroupName)
    assert not response.data.upVote.upvote

    response = get_vote_query(client, dataset_fixture.datasetUri, 'dataset', dataset_fixture.SamlAdminGroupName)
    assert not response.data.getVote.upvote

    response = count_votes_query(client, dataset_fixture.datasetUri, 'dataset', dataset_fixture.SamlAdminGroupName)
    assert response.data.countUpVotes == 0
