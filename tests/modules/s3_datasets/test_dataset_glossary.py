from typing import List

from dataall.modules.catalog.db.glossary_models import TermLink
from dataall.modules.s3_datasets.db.dataset_models import DatasetTableColumn
from tests.modules.catalog.test_glossary import *


@pytest.fixture(scope='module', autouse=True)
def _columns(db, dataset_fixture, table_fixture) -> List[DatasetTableColumn]:
    with db.scoped_session() as session:
        cols = []
        for i in range(0, 10):
            c = DatasetTableColumn(
                datasetUri=dataset_fixture.datasetUri,
                tableUri=table_fixture.tableUri,
                label=f'c{i + 1}',
                AWSAccountId=dataset_fixture.restricted.AwsAccountId,
                region=dataset_fixture.restricted.region,
                GlueTableName='table',
                typeName='String',
                owner='user',
                GlueDatabaseName=dataset_fixture.restricted.GlueDatabaseName,
            )
            session.add(c)
            cols.append(c)
    yield cols


def test_dataset_term_link_approval(db, client, t1, dataset_fixture, user, group):
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
        datasetUri=dataset_fixture.datasetUri,
        input={'terms': [t1.nodeUri], 'KmsAlias': ''},
    )
    with db.scoped_session() as session:
        link: TermLink = session.query(TermLink).filter(TermLink.nodeUri == t1.nodeUri).first()
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
    link: TermLink = session.query(TermLink).get(link.linkUri)
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
    link: TermLink = session.query(TermLink).get(link.linkUri)
    assert not link.approvedBySteward


def test_get_column_term_associations(t1, dataset_fixture, group, db, client):
    r = client.query(
        """
        query GetDataset($datasetUri: String!) {
          getDataset(datasetUri: $datasetUri) {
            datasetUri
            owner
            description
            terms {
              count
              nodes {
                __typename
                ... on Term {
                  nodeUri
                  path
                  label
                }
              }
            }
          }
        }
        """,
        datasetUri=dataset_fixture.datasetUri,
        username='alice',
        groups=[group.name],
    )
    assert r.data.getDataset.terms.nodes[0].nodeUri == t1.nodeUri
    assert r.data.getDataset.terms.nodes[0].label == t1.label
