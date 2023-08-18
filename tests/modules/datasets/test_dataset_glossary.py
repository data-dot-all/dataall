from typing import List

from dataall.modules.catalog.db.glossary_models import TermLink
from dataall.modules.datasets_base.db.models import DatasetTableColumn
from tests.modules.catalog.test_glossary import *


@pytest.fixture(scope='module', autouse=True)
def _columns(db, dataset_fixture, table_fixture) -> List[DatasetTableColumn]:
    with db.scoped_session() as session:
        cols = []
        for i in range(0, 10):
            c = DatasetTableColumn(
                datasetUri=dataset_fixture.datasetUri,
                tableUri=table_fixture.tableUri,
                label=f'c{i+1}',
                AWSAccountId=dataset_fixture.AwsAccountId,
                region=dataset_fixture.region,
                GlueTableName='table',
                typeName='String',
                owner='user',
                GlueDatabaseName=dataset_fixture.GlueDatabaseName,
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
        input={
            'terms': [t1.nodeUri],
            'KmsAlias': ''
        },
    )
    with db.scoped_session() as session:
        link: TermLink = (
            session.query(TermLink)
            .filter(TermLink.nodeUri == t1.nodeUri)
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


def test_get_column_term_associations(t1, db, client):
    r = client.query(
        """
        query GetTerm($nodeUri:String!){
            getTerm(nodeUri:$nodeUri){
                nodeUri
                label
                readme
                associations{
                    count
                    nodes{
                        linkUri
                        target{
                            ... on DatasetTableColumn{
                                label
                                columnUri
                            }
                        }
                    }
                }
            }

        }
        """,
        nodeUri=t1.nodeUri,
        username='alice',
    )
    assert r.data.getTerm.nodeUri == t1.nodeUri
    assert r.data.getTerm.label == t1.label
    assert r.data.getTerm.readme == t1.readme
