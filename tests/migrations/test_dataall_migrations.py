from unittest.mock import MagicMock
from assertpy import assert_that
from migrations.dataall_migrations.migrationmanager import MigrationManager
from migrations.dataall_migrations.base_migration import MigrationBase


def get_migration(revision_id, next_migration, up=None, down=None):
    mock_name = f'Migration{revision_id}'
    migration = MagicMock(name=mock_name, spec=MigrationBase)
    migration.next_migration.return_value = next_migration
    migration.revision_id.return_value = revision_id
    migration.__name__ = mock_name
    migration.up.side_effect = up
    migration.down.side_effect = down
    return migration


def test_up_and_down():
    m2 = get_migration('2', None)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    manager = MigrationManager('0', m0)
    manager.upgrade()
    manager.downgrade()

    assert_that(manager.current_migration.revision_id()).is_equal_to('0')


def test_partial_up_and_down():
    m2 = get_migration('2', None)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    manager = MigrationManager('1', m0)
    manager.upgrade()
    m0.up.assert_not_called()
    m1.up.assert_not_called()
    m2.up.assert_called_once()

    manager.downgrade()

    m0.down.assert_not_called()
    m1.down.assert_called_once()
    m2.down.assert_called_once()


def test_dont_call_current_migration():
    m2 = get_migration('2', None)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    manager = MigrationManager('0', m0)
    new_version = manager.upgrade()

    m0.up.assert_not_called()
    m1.up.assert_called_once()
    m2.up.assert_called_once()

    assert_that(new_version).is_equal_to('2')


def test_dataall_partial_upgrade_success():
    m3 = get_migration('3', None)
    m2 = get_migration('2', m3)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    # upgrade to the middle
    manager = MigrationManager('1', m0)
    new_version = manager.upgrade('2')

    m0.up.assert_not_called()
    m1.up.assert_not_called()
    m2.up.assert_called_once()
    m3.up.assert_not_called()

    assert_that(new_version).is_equal_to('2')

    # continue upgrade to the end with the same manager
    new_version = manager.upgrade()

    m0.up.assert_not_called()
    m1.up.assert_not_called()
    m2.up.assert_called_once()
    m3.up.assert_called_once()

    assert_that(new_version).is_equal_to('3')


def test_incorrect_current_revison_key():
    incorrect_key = 'incorrect'

    m3 = get_migration('3', None)
    m2 = get_migration('2', m3)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    assert_that(MigrationManager).raises(Exception).when_called_with(incorrect_key, m0).contains(
        f'Revision {incorrect_key} is not found'
    )


def test_incorrect_upgrade_revison_key():
    incorrect_key = 'incorrect'

    m3 = get_migration('3', None)
    m2 = get_migration('2', m3)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    manager = MigrationManager('0', m0)

    assert_that(manager.upgrade).raises(Exception).when_called_with(incorrect_key).contains(
        f'Failed to find {incorrect_key}.'
    )


def test_update_rollback():
    m3 = get_migration('3', None)
    m2 = get_migration('2', m3, up=Exception('Test'))
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    manager = MigrationManager('0', m0)
    new_revision = manager.upgrade()

    assert_that(new_revision).is_false()
    assert_that(manager.current_migration.revision_id()).is_equal_to('0')
    m0.up.assert_not_called()
    m1.up.assert_called_once()
    m2.up.assert_called_once()
    m3.up.assert_not_called()

    m0.down.assert_not_called()
    m1.down.assert_called_once()
    m2.down.assert_not_called()
    m3.down.assert_not_called()


def test_dataall_full_downrade_success():
    m2 = get_migration('2', None)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    manager = MigrationManager('2', m0)
    new_version = manager.downgrade()

    m0.down.assert_not_called()
    m1.down.assert_called_once()
    m2.down.assert_called_once()

    assert_that(new_version).is_equal_to('0')


def test_dataall_partial_downrade_success():
    m3 = get_migration('3', None)
    m2 = get_migration('2', m3)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    # upgrade to the middle
    manager = MigrationManager('3', m0)
    new_version = manager.downgrade('2')

    m0.down.assert_not_called()
    m1.down.assert_not_called()
    m2.down.assert_not_called()

    m3.down.assert_called_once()

    assert_that(new_version).is_equal_to('2')

    # continue upgrade to the end with the same manager
    new_version = manager.downgrade()

    m0.down.assert_not_called()
    m3.down.assert_called_once()
    m2.down.assert_called_once()
    m1.down.assert_called_once()

    assert_that(new_version).is_equal_to('0')


def test_incorrect_downgrade_revison_key():
    m3 = get_migration('3', None)
    m2 = get_migration('2', m3)
    m1 = get_migration('1', m2)
    m0 = get_migration('0', m1)

    # upgrade to the middle
    manager = MigrationManager('3', m0)
    incorrect_key = 'incorrect'

    assert_that(manager.downgrade).raises(Exception).when_called_with(incorrect_key).contains(
        f'Failed to find {incorrect_key}'
    )


def test_downgrade_rollback():
    m3 = get_migration('3', None)
    m2 = get_migration('2', m3)
    m1 = get_migration('1', m2, down=Exception('Test'))
    m0 = get_migration('0', m1)

    # upgrade to the middle
    manager = MigrationManager('3', m0)
    new_revision = manager.downgrade()

    assert_that(new_revision).is_false()
    assert_that(manager.current_migration.revision_id()).is_equal_to('3')
    m0.up.assert_not_called()
    m1.up.assert_not_called()
    m2.up.assert_called_once()
    m3.up.assert_called_once()

    m0.down.assert_not_called()
    m1.down.assert_called_once()
    m2.down.assert_called_once()
    m3.down.assert_called_once()
