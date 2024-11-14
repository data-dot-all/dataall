from unittest.mock import MagicMock
import pytest
from assertpy import assert_that
from dataall.base.api import bootstrap
from dataall.base.loader import load_modules, ImportMode
from dataall.base.context import RequestContext
from threading import local
from dataall.base.db.exceptions import TenantUnauthorized
import inspect

from pytest import fixture

load_modules(modes={ImportMode.API})

CHECK_PERMS = ['archiveOrganization']


@fixture(scope='function')
def patch_context(mocker, db, userNoTenantPermissions, groupNoTenantPermissions):
    mock = local()
    mock.context = RequestContext(
        db, userNoTenantPermissions.username, [groupNoTenantPermissions.groupUri], userNoTenantPermissions
    )
    mocker.patch('dataall.base.context._request_storage', mock)


@pytest.mark.parametrize(
    'name,field_resolver',
    [
        (f'{_type.name}.{field.name}', field.resolver)
        for _type in bootstrap().types
        for field in _type.fields
        if field.resolver and _type.name in ['Mutation', 'Query'] and field.name in CHECK_PERMS
    ],
)
def test_unauthorized_tenant_permissions(name, field_resolver, patch_context):
    iargs = {arg: MagicMock() for arg in inspect.signature(field_resolver).parameters.keys()}
    assert_that(field_resolver).raises(TenantUnauthorized).when_called_with(**iargs).contains('UnauthorizedOperation')
