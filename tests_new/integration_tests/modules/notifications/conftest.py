import pytest

from tests_new.integration_tests.modules.share_base.queries import (
    submit_share_object,
    add_share_item,
    get_share_object,
    remove_shared_item,
)


@pytest.fixture(scope='module')
def session_share_1_notifications(client5, session_share_1):
    share_item_uri = None
    try:
        updated_share = get_share_object(client5, session_share_1.shareUri)
        item_to_add = updated_share['items'].nodes[0]
        share_item_uri = add_share_item(client5, session_share_1.shareUri, item_to_add.itemUri, item_to_add.itemType)
        submit_share_object(client5, session_share_1.shareUri)
        yield session_share_1
    finally:
        if share_item_uri:
            remove_shared_item(client5, share_item_uri)
