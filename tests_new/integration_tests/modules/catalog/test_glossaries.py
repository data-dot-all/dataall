from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.catalog.queries import (
    create_glossary,
    get_glossary,
    get_glossary_tree,
    list_glossary_associations,
    list_glossaries,
    search_glossary,
    delete_glossary,
    update_glossary,
    create_term,
    delete_term,
    update_term,
    create_category,
    delete_category,
    update_category,
    approve_term_association,
    dismiss_term_association,
    start_reindex_catalog,
)


def test_create_glossary(client1, glossary1, session_id):
    assert_that(glossary1.nodeUri).is_not_none()
    assert_that(glossary1.label).is_equal_to(f'glossary1-{session_id}')
    assert_that(glossary1.readme).is_equal_to('Glossary created for integration testing')


def test_get_glossary(client1, glossary1, category1, glossary_term1, category_term1, session_id):
    response = get_glossary(client1, node_uri=glossary1.nodeUri)
    assert_that(response.label).is_equal_to(f'glossary1-{session_id}')
    assert_that(response.nodeUri).is_equal_to(glossary1.nodeUri)
    assert_that(response.stats).contains_entry(categories=1, terms=2)


def test_get_glossary_get_tree(client1, glossary1, category1, glossary_term1, category_term1):
    response = get_glossary_tree(client1, node_uri=glossary1.nodeUri)
    assert_that(response.tree).is_not_none()
    assert_that(response.tree.count).is_equal_to(4)
    # Check that the glossary is in the tree
    glos = next((n for n in response.tree.nodes if n.nodeUri == glossary1.nodeUri), None)
    assert_that(glos.label).is_equal_to(glossary1.label)
    assert_that(glos.nodeUri).is_equal_to(glossary1.nodeUri)
    assert_that(glos.path).is_equal_to(f'/{glossary1.nodeUri}')
    # Check that the category is in the tree
    cat = next((n for n in response.tree.nodes if n.nodeUri == category1.nodeUri), None)
    assert_that(cat.label).is_equal_to(category1.label)
    assert_that(cat.nodeUri).is_equal_to(category1.nodeUri)
    assert_that(cat.parentUri).is_equal_to(glossary1.nodeUri)
    assert_that(cat.path).is_equal_to(f'/{glossary1.nodeUri}/{category1.nodeUri}')
    # Check that the terms are in the tree and their parentUris are correct
    g_term = next((n for n in response.tree.nodes if n.nodeUri == glossary_term1.nodeUri), None)
    assert_that(g_term.label).is_equal_to(glossary_term1.label)
    assert_that(g_term.nodeUri).is_equal_to(glossary_term1.nodeUri)
    assert_that(g_term.parentUri).is_equal_to(glossary1.nodeUri)
    assert_that(g_term.path).is_equal_to(f'/{glossary1.nodeUri}/{glossary_term1.nodeUri}')
    c_term = next((n for n in response.tree.nodes if n.nodeUri == category_term1.nodeUri), None)
    assert_that(c_term.label).is_equal_to(category_term1.label)
    assert_that(c_term.nodeUri).is_equal_to(category_term1.nodeUri)
    assert_that(c_term.parentUri).is_equal_to(category1.nodeUri)
    assert_that(c_term.path).is_equal_to(f'/{glossary1.nodeUri}/{category1.nodeUri}/{category_term1.nodeUri}')


def test_get_glossary_list_associations(client1, glossary1, glossary_term1, dataset_association1):
    response = list_glossary_associations(client1, node_uri=glossary1.nodeUri)
    assert_that(response.associations.count).is_equal_to(1)
    ass = response.associations.nodes[0]
    assert_that(ass.linkUri).is_not_none()
    assert_that(ass.term.nodeUri).is_equal_to(glossary_term1.nodeUri)


def test_list_glossaries(client1, glossary1, category1, glossary_term1, category_term1):
    response = list_glossaries(client1)
    assert_that(response.count).is_greater_than_or_equal_to(1)
    glos_1 = next((n for n in response.nodes if n.nodeUri == glossary1.nodeUri), None)
    assert_that(glos_1.nodeUri).is_equal_to(glossary1.nodeUri)
    assert_that(glos_1.stats).contains_entry(categories=1, terms=2)


def test_search_glossary(client1, glossary1, category1, glossary_term1, category_term1):
    response = search_glossary(client1, term=glossary1.label)
    assert_that(response.count).is_equal_to(1)


def test_update_glossary_unauthorized(client2, group2, glossary1):
    assert_that(update_glossary).raises(GqlError).when_called_with(
        client2,
        node_uri=glossary1.nodeUri,
        name='glossaryUpdated',
        group=group2,
        read_me='dummy',
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_update_glossary(client1, group1, glossary1, session_id):
    response = update_glossary(
        client1,
        node_uri=glossary1.nodeUri,
        name='glossaryUpdated',
        group=group1,
        read_me=f'UPDATED: {session_id} Glossary created for integration testing',
    )
    assert_that(response.label).is_equal_to('glossaryUpdated')
    assert_that(response.readme).is_equal_to(f'UPDATED: {session_id} Glossary created for integration testing')


def test_delete_glossary_unauthorized(client2, group2, glossary1):
    assert_that(delete_glossary).raises(GqlError).when_called_with(client2, glossary1.nodeUri).contains(
        'UnauthorizedOperation', 'GLOSSARY MUTATION'
    )


def test_delete_glossary(client1, group1):
    glos = create_glossary(client1, name='glossary1', group=group1, read_me='Glossary created for integration testing')
    number_glossaries_before_delete = list_glossaries(client1).count
    response = delete_glossary(client1, glos.nodeUri)
    assert_that(response).is_true()
    response = list_glossaries(client1)
    assert_that(response.count).is_equal_to(number_glossaries_before_delete - 1)


def test_delete_glossary_with_categories_and_terms(client1, group1):
    glos = create_glossary(client1, name='glossary1', group=group1, read_me='Glossary created for integration testing')
    category = create_category(
        client1, name='category1', parent_uri=glos.nodeUri, read_me='Category created for integration testing'
    )
    term = create_term(
        client1, name='term1', parent_uri=category.nodeUri, read_me='Term created for integration testing'
    )
    response = delete_glossary(client1, glos.nodeUri)
    assert_that(response).is_true()


def test_create_category(client1, category1):
    assert_that(category1.nodeUri).is_not_none()
    assert_that(category1.label).is_equal_to('category1')


def test_update_category_unauthorized(client2, group2, category1):
    assert_that(update_category).raises(GqlError).when_called_with(
        client2,
        node_uri=category1.nodeUri,
        name=category1.label,
        read_me='dummy',
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_update_category(client1, category1, session_id):
    response = update_category(
        client1,
        node_uri=category1.nodeUri,
        name=category1.label,
        read_me=f'UPDATED: {session_id} Category created for integration testing',
    )
    assert_that(response.readme).is_equal_to(f'UPDATED: {session_id} Category created for integration testing')


def test_delete_category_unauthorized(client2, group2, category1):
    assert_that(delete_category).raises(GqlError).when_called_with(
        client2,
        category1.nodeUri,
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_delete_category(client1, glossary1):
    category = create_category(
        client1, name='glossary1', parent_uri=glossary1.nodeUri, read_me='Category created for integration testing'
    )
    number_categories_before_delete = get_glossary(client1, node_uri=glossary1.nodeUri).stats.categories
    response = delete_category(client1, category.nodeUri)
    assert_that(response).is_true()
    response = get_glossary(client1, node_uri=glossary1.nodeUri)
    assert_that(response.stats.categories).is_equal_to(number_categories_before_delete - 1)


def test_delete_category_with_terms(client1, glossary1):
    category = create_category(
        client1, name='category1', parent_uri=glossary1.nodeUri, read_me='Category created for integration testing'
    )
    term = create_term(
        client1, name='term1', parent_uri=category.nodeUri, read_me='Term created for integration testing'
    )
    response = delete_category(client1, node_uri=category.nodeUri)
    assert_that(response).is_true()


def test_create_term_in_glossary_unauthorized(client2, glossary1):
    assert_that(create_term).raises(GqlError).when_called_with(
        client2, name='glos_term1', parent_uri=glossary1.nodeUri, read_me='Term created for integration testing'
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_create_term_in_glossary(client1, glossary_term1):
    assert_that(glossary_term1.nodeUri).is_not_none()
    assert_that(glossary_term1.label).is_equal_to('glos_term1')


def test_create_term_in_category_unauthorized(client2, category1):
    assert_that(create_term).raises(GqlError).when_called_with(
        client2, name='glos_term1', parent_uri=category1.nodeUri, read_me='Term created for integration testing'
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_create_term_in_category(client1, category_term1):
    assert_that(category_term1.nodeUri).is_not_none()
    assert_that(category_term1.label).is_equal_to('cat_term1')


def test_update_term_unauthorized(client2, glossary_term1):
    assert_that(update_term).raises(GqlError).when_called_with(
        client2,
        node_uri=glossary_term1.nodeUri,
        name=glossary_term1.label,
        read_me='Dummy',
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_update_term(client1, glossary_term1, session_id):
    response = update_term(
        client1,
        node_uri=glossary_term1.nodeUri,
        name=glossary_term1.label,
        read_me=f'UPDATED: {session_id} Glossary term created for integration testing',
    )
    assert_that(response.readme).is_equal_to(f'UPDATED: {session_id} Glossary term created for integration testing')


def test_delete_term_unauthorized(client2, glossary_term1):
    assert_that(delete_term).raises(GqlError).when_called_with(
        client2,
        glossary_term1.nodeUri,
    ).contains('UnauthorizedOperation', 'GLOSSARY MUTATION')


def test_delete_term(client1, group1, category1, glossary1):
    term = create_term(
        client1, name='toDelete', parent_uri=category1.nodeUri, read_me='Term created for integration testing'
    )
    number_terms_before_delete = get_glossary(client1, node_uri=glossary1.nodeUri).stats.terms
    response = delete_term(client1, node_uri=term.nodeUri)
    assert_that(response).is_true()
    response = get_glossary(client1, node_uri=glossary1.nodeUri)
    assert_that(response.stats.terms).is_equal_to(number_terms_before_delete - 1)


def test_approve_term_association_unauthorized(client2, dataset_association1):
    assert_that(approve_term_association).raises(GqlError).when_called_with(
        client2, link_uri=dataset_association1.linkUri
    ).contains('UnauthorizedOperation', 'ASSOCIATE_GLOSSARY_TERM')


def test_approve_term_association(approved_dataset_association1, dataset_association1):
    assert_that(approved_dataset_association1.linkUri).is_equal_to(dataset_association1.linkUri)
    assert_that(approved_dataset_association1.approvedBySteward).is_equal_to(True)


def test_dismiss_term_association_unauthorized(client2, approved_dataset_association1):
    assert_that(dismiss_term_association).raises(GqlError).when_called_with(
        client2, link_uri=approved_dataset_association1.linkUri
    ).contains('UnauthorizedOperation', 'ASSOCIATE_GLOSSARY_TERM')


def test_dismiss_term_association(client1, glossary1, approved_dataset_association1):
    assert_that(approved_dataset_association1.approvedBySteward).is_equal_to(True)
    response = dismiss_term_association(client1, link_uri=approved_dataset_association1.linkUri)
    assert_that(response).is_true()
    response = list_glossary_associations(client1, node_uri=glossary1.nodeUri)
    association = next(
        (n for n in response.associations.nodes if n.linkUri == approved_dataset_association1.linkUri), None
    )
    assert_that(association.approvedBySteward).is_equal_to(False)


def test_start_reindex_catalog_unauthorized(client1):
    assert_that(start_reindex_catalog).raises(GqlError).when_called_with(client1, handle_deletes=True).contains(
        'Only data.all admin', 're-index catalog'
    )


def test_start_reindex_catalog_handle_deletes(clientTenant):
    response = start_reindex_catalog(clientTenant, handle_deletes=True)
    assert_that(response).is_true()


def test_start_reindex_catalog_handle_deletes_false(clientTenant):
    response = start_reindex_catalog(clientTenant, handle_deletes=False)
    assert_that(response).is_true()
