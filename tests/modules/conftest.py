import pytest

from dataall.core.permissions.db import Tenant


@pytest.fixture(scope='module')
def tenant(db):
    with db.scoped_session() as session:
        tenant = Tenant.save_tenant(
            session, name='dataall', description='Tenant dataall'
        )
        yield tenant


@pytest.fixture(scope='module', autouse=True)
def patch_es(module_mocker):
    module_mocker.patch('dataall.base.searchproxy.connect', return_value={})
    module_mocker.patch('dataall.base.searchproxy.search', return_value={})
    module_mocker.patch('dataall.modules.catalog.indexers.base_indexer.BaseIndexer.delete_doc', return_value={})
    module_mocker.patch('dataall.modules.catalog.indexers.base_indexer.BaseIndexer._index', return_value={})
