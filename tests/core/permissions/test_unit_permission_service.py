from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.resources_permissions import RESOURCES_ALL_WITH_DESC
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL_WITH_DESC


@pytest.fixture
def save_permission_mock():
    with patch(
        'dataall.core.permissions.services.permission_service.PermissionService.save_permission'
    ) as save_permission:
        save_permission.side_effect = lambda session, name, description, permission_type: Permission(
            name=name, description=description, type=permission_type
        )
        yield save_permission


def test_init_permissions_all_preexist(save_permission_mock):
    session_mock = MagicMock(Session)
    session_mock.query.return_value.filter.return_value.all.return_value = [
        Permission(name=name) for name in list(RESOURCES_ALL_WITH_DESC.keys()) + list(TENANT_ALL_WITH_DESC.keys())
    ]
    inserted_perms = PermissionService.init_permissions(session_mock)
    assert not inserted_perms


def test_init_permissions_resources_preexist(save_permission_mock):
    session_mock = MagicMock(Session)
    session_mock.query.return_value.filter.return_value.all.return_value = [
        Permission(name=name) for name in list(TENANT_ALL_WITH_DESC.keys())
    ]
    inserted_perms = [perm.name for perm in PermissionService.init_permissions(session_mock)]
    assert all(perm in inserted_perms for perm in RESOURCES_ALL_WITH_DESC.keys())


def test_init_permissions_tenant_preexist(save_permission_mock):
    session_mock = MagicMock(Session)
    session_mock.query.return_value.filter.return_value.all.return_value = [
        Permission(name=name) for name in list(RESOURCES_ALL_WITH_DESC.keys())
    ]
    inserted_perms = [perm.name for perm in PermissionService.init_permissions(session_mock)]
    assert all(perm in inserted_perms for perm in TENANT_ALL_WITH_DESC.keys())


@patch('dataall.core.permissions.services.permission_service.logger')
def test_init_permissions_warn_dups(logger_mock: MagicMock, save_permission_mock):
    session_mock = MagicMock(Session)
    session_mock.query.return_value.filter.return_value.all.return_value = [
        Permission(name='DUP_PERM'),
        Permission(name='DUP_PERM'),
    ]
    PermissionService.init_permissions(session_mock)
    assert 'permission appears' in str(logger_mock.warning.call_args_list)
