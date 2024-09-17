import pytest
from integration_tests.modules.catalog.queries import (
    create_glossary,
    delete_glossary,
    create_term,
    delete_term,
    create_category,
    delete_category,
    list_glossary_associations,
)

from integration_tests.modules.s3_datasets.queries import update_dataset

"""
Temp glossary elements. Scope=function
"""


@pytest.fixture(scope='function')
def glossary1(client1, group1):
    glos = None
    try:
        glos = create_glossary(
            client1, name='glossary1', group=group1, read_me='Glossary created for integration testing'
        )
        yield glos
    finally:
        if glos:
            delete_glossary(client1, node_uri=glos.nodeUri)


@pytest.fixture(scope='function')
def category1(client1, group1, glossary1):
    cat = None
    try:
        cat = create_category(
            client1, name='category1', parent_uri=glossary1.nodeUri, read_me='Category created for integration testing'
        )
        yield cat
    finally:
        if cat:
            delete_category(client1, node_uri=cat.nodeUri)


@pytest.fixture(scope='function')
def glossary_term1(client1, group1, glossary1):
    term = None
    try:
        term = create_term(
            client1, name='glos_term1', parent_uri=glossary1.nodeUri, read_me='Term created for integration testing'
        )
        yield term
    finally:
        if term:
            delete_term(client1, node_uri=term.nodeUri)


@pytest.fixture(scope='function')
def category_term1(client1, group1, category1):
    term = None
    try:
        term = create_term(
            client1, name='cat_term1', parent_uri=category1.nodeUri, read_me='Term created for integration testing'
        )
        yield term
    finally:
        if term:
            delete_term(client1, node_uri=term.nodeUri)


"""
Session glossary elements needed if using associations

WARNING!
Associations are applied to the S3_Datasets module
Glossaries can only be tested if the S3_datasets module is enabled in the deployment used for testing!
"""


@pytest.fixture(scope='session')
def session_glossary1(client1, group1):
    glos = None
    try:
        glos = create_glossary(
            client1, name='Sesssion glossary1', group=group1, read_me='Glossary created for integration testing'
        )
        yield glos
    finally:
        if glos:
            delete_glossary(client1, node_uri=glos.nodeUri)


@pytest.fixture(scope='session')
def session_glossary_term1(client1, group1, session_glossary1):
    term = None
    try:
        term = create_term(
            client1,
            name='Session glos_term1',
            parent_uri=session_glossary1.nodeUri,
            read_me='Term created for integration testing',
        )
        yield term
    finally:
        if term:
            delete_term(client1, node_uri=term.nodeUri)


@pytest.fixture(scope='session')
def dataset_association_with_glossary_term1(
    client1, group1, session_glossary1, session_glossary_term1, session_s3_dataset1
):
    update_dataset(
        client1,
        datasetUri=session_s3_dataset1.datasetUri,
        input={
            'terms': [session_glossary_term1.nodeUri],
            'label': session_s3_dataset1.label,
            'description': session_s3_dataset1.description,
            'tags': session_s3_dataset1.tags,
            'stewards': session_s3_dataset1.stewards,
            'topics': session_s3_dataset1.topics,
            'confidentiality': session_s3_dataset1.confidentiality,
            'autoApprovalEnabled': False,
            'enableExpiration': False,
            'KmsAlias': session_s3_dataset1.KmsAlias,
        },
    )
    response = list_glossary_associations(client1, node_uri=session_glossary1.nodeUri)
    ds_association = next(
        (assoc for assoc in response.associations.nodes if assoc.targetUri == session_s3_dataset1.datasetUri), None
    )
    yield ds_association
