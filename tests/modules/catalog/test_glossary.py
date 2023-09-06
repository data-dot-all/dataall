from datetime import datetime

from dataall.modules.catalog.db.glossary_models import GlossaryNode
import pytest


@pytest.fixture(scope='module', autouse=True)
def g1(client, group):
    r = client.query(
        """
        mutation CreateGlossary($input:CreateGlossaryInput){
            createGlossary(input:$input){
                nodeUri
                label
                readme
            }
        }
        """,
        input={
            'label': 'Customer Glossary',
            'admin': group.name,
            'readme': 'Glossary of customer related data',
        },
        username='alice',
        groups=[group.name],
    )
    yield r.data.createGlossary


@pytest.fixture(scope='module', autouse=True)
def c1(client, g1, group):
    r = client.query(
        """
        mutation CreateCategory(
        $parentUri:String!,
        $input:CreateCategoryInput){
            createCategory(parentUri:$parentUri,input:$input){
                nodeUri
                label
                readme
            }
        }
        """,
        parentUri=g1.nodeUri,
        input={'label': 'Identifiers', 'readme': 'Customer identifiers category'},
        username='alice',
        groups=[group.name],
    )
    yield r.data.createCategory


@pytest.fixture(scope='module', autouse=True)
def subcategory(client, c1, group):
    r = client.query(
        """
        mutation CreateCategory(
            $parentUri:String!
            $input:CreateCategoryInput!
        ){
            createCategory(parentUri:$parentUri,input:$input){
                nodeUri
                label
                readme
                created
           }
        }
        """,
        input={
            'label': 'OptionalIdentifiers',
            'readme': 'Additional, non required customer identifiers',
        },
        parentUri=c1.nodeUri,
        username='alice',
        groups=[group.name],
    )
    subcategory = r.data.createCategory
    yield subcategory


@pytest.fixture(scope='module', autouse=True)
def t1(client, c1, group):
    r = client.query(
        """
        mutation CreateTerm(
        $parentUri:String!,
        $input:CreateTermInput){
            createTerm(parentUri:$parentUri,input:$input){
                nodeUri
                label
                readme
            }
        }
        """,
        parentUri=c1.nodeUri,
        input={'label': 'Customer ID', 'readme': 'Global Customer Identifier'},
        username='alice',
        groups=[group.name],
    )
    yield r.data.createTerm


def test_list_glossaries(client):
    response = client.query(
        """
        query ListGlossaries{
            listGlossaries{
                count
                nodes{
                    nodeUri
                    children{
                        count
                        nodes{
                            __typename
                            ... on Category{
                                label
                                nodeUri
                                path
                            }
                            ... on Term{
                                label
                                nodeUri
                                path
                            }
                        }
                    }
                    stats{
                        categories
                        terms
                        associations
                    }
                }
            }
        }
        """
    )
    assert response.data.listGlossaries.count == 1
    assert response.data.listGlossaries.nodes[0].stats.terms == 1
    assert response.data.listGlossaries.nodes[0].stats.categories == 2


def test_search_glossary(client):
    response = client.query(
        """
        query SearchGlossary($filter:GlossaryNodeSearchFilter){
            searchGlossary(filter:$filter){
                count
                page
                pages
                hasNext
                hasPrevious
                nodes{
                    __typename
                    ...on Glossary{
                        nodeUri
                        label
                        readme
                        created
                        owner
                        path
                    }
                    ...on Category{
                        nodeUri
                        label
                        parentUri
                        readme
                        created
                        owner
                        path
                    }
                    ...on Term{
                        nodeUri
                        parentUri
                        label
                        readme
                        created
                        owner
                        path
                    }

                }
            }
        }
        """
    )
    assert response.data.searchGlossary.count == 4


def test_get_glossary(client, g1):
    r = client.query(
        """
        query GetGlossary($nodeUri:String!){
            getGlossary(nodeUri:$nodeUri){
                nodeUri
                label
                readme
            }
        }
        """,
        nodeUri=g1.nodeUri,
    )
    assert r.data.getGlossary.nodeUri == g1.nodeUri
    assert r.data.getGlossary.label == g1.label
    assert r.data.getGlossary.readme == g1.readme


def test_glossary_categories(client, g1, c1):
    r = client.query(
        """
        query GetGlossary($nodeUri:String!){
            getGlossary(nodeUri:$nodeUri){
                nodeUri
                label
                readme
                categories{
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        nodeUri
                        label
                        readme
                    }
                }
            }
        }
        """,
        nodeUri=g1.nodeUri,
    )
    assert r.data.getGlossary.categories.count == 1
    assert r.data.getGlossary.categories.nodes[0].nodeUri == c1.nodeUri


def test_update_glossary(client, g1, group):
    r = client.query(
        """
        mutation UpdateGlossary(
            $nodeUri:String!,
            $input:UpdateGlossaryInput!
        ){
            updateGlossary(
                nodeUri:$nodeUri,
                input:$input
            ){
                nodeUri
                label
                readme
            }
        }
        """,
        nodeUri=g1.nodeUri,
        input={'readme': g1.readme + '(updated description)'},
        username='alice',
        groups=[group.name],
    )
    assert r.data.updateGlossary.readme == g1.readme + '(updated description)'


def test_update_category(client, c1, group):
    r = client.query(
        """
        mutation UpdateCategory(
            $nodeUri:String!,
            $input:UpdateCategoryInput!
        ){
            updateCategory(
                nodeUri:$nodeUri,
                input:$input
            ){
                nodeUri
                label
                readme
            }
        }
        """,
        nodeUri=c1.nodeUri,
        input={'readme': c1.readme + '(updated description)'},
        username='alice',
        groups=[group.name],
    )
    assert r.data.updateCategory.readme == c1.readme + '(updated description)'


def test_delete_subcategory(client, subcategory, group):
    r = client.query(
        """
        mutation DeleteCategory(
            $nodeUri:String!,
        ){
            deleteCategory(
                nodeUri:$nodeUri,
            )
        }
        """,
        nodeUri=subcategory.nodeUri,
        username='alice',
        groups=[group.name],
    )
    print(r)


def test_delete_category(client, db, c1, group):
    now = datetime.now()
    r = client.query(
        """
        mutation DeleteCategory(
            $nodeUri:String!,
        ){
            deleteCategory(
                nodeUri:$nodeUri,
            )
        }
        """,
        nodeUri=c1.nodeUri,
        username='alice',
        groups=[group.name],
    )
    with db.scoped_session() as session:
        node = session.query(GlossaryNode).get(c1.nodeUri)
        assert node.deleted >= now


def test_list_glossaries_after_delete(client):
    response = client.query(
        """
        query ListGlossaries{
            listGlossaries{
                count
                nodes{
                    nodeUri
                    children{
                        count
                        nodes{
                            __typename
                            ... on Category{
                                label
                                nodeUri
                                path
                            }
                            ... on Term{
                                label
                                nodeUri
                                path
                            }
                        }
                    }
                    stats{
                        categories
                        terms
                        associations
                    }
                }
            }
        }
        """
    )
    assert response.data.listGlossaries.count == 1
    assert response.data.listGlossaries.nodes[0].stats.categories == 0


def test_search_glossary_after_delete(client):
    response = client.query(
        """
        query SearchGlossary($filter:GlossaryNodeSearchFilter){
            searchGlossary(filter:$filter){
                count
                page
                pages
                hasNext
                hasPrevious
                nodes{
                    __typename
                    ...on Glossary{
                        nodeUri
                        label
                        readme
                        created
                        owner
                        path
                    }
                    ...on Category{
                        nodeUri
                        label
                        parentUri
                        readme
                        created
                        owner
                        path
                    }
                    ...on Term{
                        nodeUri
                        parentUri
                        label
                        readme
                        created
                        owner
                        path
                    }

                }
            }
        }
        """
    )
    assert response.data.searchGlossary.count == 1
