import pytest

from dataall.modules.datasets import Dataset
from tests.api.test_vote import *

from dataall.db import models


@pytest.fixture(scope='module')
def org1(db, org, tenant, user, group) -> models.Organization:
    org = org('testorg', user.userName, group.name)
    yield org


@pytest.fixture(scope='module')
def env1(
    db, org1: models.Organization, user, group, env
) -> models.Environment:
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def dataset1(db, env1, org1, group, user, dataset) -> Dataset:
    yield dataset(
        org=org1, env=env1, name='dataset1', owner=user.userName, group=group.name
    )


def test_count_votes(client, dataset1):
    response = count_votes_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 0


def test_upvote(patch_es, client, dataset1):
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
        client, dataset1.datasetUri, 'dataset', False, dataset1.SamlAdminGroupName
    )
    assert not response.data.upVote.upvote

    response = get_vote_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert not response.data.getVote.upvote

    response = count_votes_query(
        client, dataset1.datasetUri, 'dataset', dataset1.SamlAdminGroupName
    )
    assert response.data.countUpVotes == 0