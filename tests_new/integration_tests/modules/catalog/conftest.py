import pytest
from integration_tests.modules.catalog.queries import (
    create_glossary,
    delete_glossary,
    create_term,
    delete_term,
    create_category,
    delete_category,
    list_glossary_associations,
    approve_term_association,
)

from integration_tests.modules.s3_datasets.queries import update_dataset

"""
Temp glossary elements. Scope=function
"""


@pytest.fixture(scope='function')
def glossary1(client1, group1, session_id):
    glos = None
    try:
        glos = create_glossary(
            client1, name=f'glossary1-{session_id}', group=group1, read_me='Glossary created for integration testing'
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
WARNING!
Associations are applied to the S3_Datasets module
Glossaries can only be tested if the S3_datasets module is enabled in the deployment used for testing!
"""


@pytest.fixture(scope='function')
def dataset_association1(client1, group1, glossary1, glossary_term1, session_s3_dataset1):
    ds_association = None
    try:
        update_dataset(
            client1,
            datasetUri=session_s3_dataset1.datasetUri,
            input={
                'terms': [glossary_term1.nodeUri],
                'KmsAlias': session_s3_dataset1.restricted.KmsAlias,
            },
        )
        response = list_glossary_associations(client1, node_uri=glossary1.nodeUri)
        ds_association = next(
            (assoc for assoc in response.associations.nodes if assoc.targetUri == session_s3_dataset1.datasetUri), None
        )
        yield ds_association
    finally:
        if ds_association:
            update_dataset(
                client1,
                datasetUri=session_s3_dataset1.datasetUri,
                input={
                    'terms': [],
                    'KmsAlias': session_s3_dataset1.restricted.KmsAlias,
                },
            )


@pytest.fixture(scope='function')
def approved_dataset_association1(client1, glossary1, dataset_association1):
    approve_term_association(client1, link_uri=dataset_association1.linkUri)
    response = list_glossary_associations(client1, node_uri=glossary1.nodeUri)
    association = next((n for n in response.associations.nodes if n.linkUri == dataset_association1.linkUri), None)
    yield association
