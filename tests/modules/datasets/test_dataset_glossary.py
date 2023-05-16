import pytest
from typing import List

from dataall.db.models import Environment, Organization
from dataall.modules.datasets_base.db.models import DatasetTableColumn, DatasetTable, Dataset
from tests.api.test_glossary import *


@pytest.fixture(scope='module')
def _org(db, org, tenant, user, group) -> Organization:
    org = org('testorg', user.userName, group.name)
    yield org


@pytest.fixture(scope='module')
def _env(db, _org: Organization, user, group, env) -> Environment:
    env1 = env(_org, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def _dataset(db, _env, _org, group, user, dataset) -> Dataset:
    with db.scoped_session() as session:
        yield dataset(
            org=_org, env=_env, name='dataset1', owner=user.userName, group=group.name
        )


@pytest.fixture(scope='module', autouse=True)
def _table(db, _dataset) -> DatasetTable:
    with db.scoped_session() as session:
        t = DatasetTable(
            datasetUri=_dataset.datasetUri,
            label='table',
            AWSAccountId=_dataset.AwsAccountId,
            region=_dataset.region,
            S3BucketName=_dataset.S3BucketName,
            S3Prefix='/raw',
            GlueTableName='table',
            owner='alice',
            GlueDatabaseName=_dataset.GlueDatabaseName,
        )
        session.add(t)
    yield t


@pytest.fixture(scope='module', autouse=True)
def _columns(db, _dataset, _table) -> List[DatasetTableColumn]:
    with db.scoped_session() as session:
        cols = []
        for i in range(0, 10):
            c = DatasetTableColumn(
                datasetUri=_dataset.datasetUri,
                tableUri=_table.tableUri,
                label=f'c{i+1}',
                AWSAccountId=_dataset.AwsAccountId,
                region=_dataset.region,
                GlueTableName='table',
                typeName='String',
                owner='user',
                GlueDatabaseName=_dataset.GlueDatabaseName,
            )
            session.add(c)
            cols.append(c)
    yield cols


def test_dataset_link_term(client, t1, _columns, group):
    col = _columns[0]
    r = client.query(
        """
        mutation LinkTerm(
            $nodeUri:String!,
            $targetUri:String!,
            $targetType:String!,
        ){
            linkTerm(
                nodeUri:$nodeUri,
                targetUri:$targetUri,
                targetType:$targetType
            ){
                linkUri
            }
        }
        """,
        nodeUri=t1.nodeUri,
        targetUri=col.columnUri,
        targetType='Column',
        username='alice',
        groups=[group.name],
    )
    link_uri = r.data.linkTerm.linkUri

    r = client.query(
        """
        query GetGlossaryTermLink($linkUri:String!){
            getGlossaryTermLink(linkUri:$linkUri){
                linkUri
                created
                target{
                    __typename
                    ... on DatasetTableColumn{
                         label
                        columnUri
                    }
                }
            }
        }
        """,
        linkUri=link_uri,
        username='alice',
    )
    print(r)


def test_dataset_term_link_approval(db, client, t1, _dataset, user, group):
    response = client.query(
        """
        mutation UpdateDataset($datasetUri:String!,$input:ModifyDatasetInput){
            updateDataset(datasetUri:$datasetUri,input:$input){
                datasetUri
                label
                tags
            }
        }
        """,
        username='alice',
        groups=[group.name],
        datasetUri=_dataset.datasetUri,
        input={'terms': [t1.nodeUri]},
    )
    with db.scoped_session() as session:
        link: models.TermLink = (
            session.query(models.TermLink)
            .filter(models.TermLink.nodeUri == t1.nodeUri)
            .first()
        )
    r = client.query(
        """
        mutation ApproveTermAssociation($linkUri:String!){
            approveTermAssociation(linkUri:$linkUri)
        }
        """,
        linkUri=link.linkUri,
        username='alice',
        groups=[group.name],
    )
    assert r
    link: models.TermLink = session.query(models.TermLink).get(link.linkUri)
    assert link.approvedBySteward

    r = client.query(
        """
        mutation DismissTermAssociation($linkUri:String!){
            dismissTermAssociation(linkUri:$linkUri)
        }
        """,
        linkUri=link.linkUri,
        username='alice',
        groups=[group.name],
    )
    assert r
    link: models.TermLink = session.query(models.TermLink).get(link.linkUri)
    assert not link.approvedBySteward
