from migrations.dataall_migrations.migrationmanager import MigrationManager
from tests.migrations.migrations_classes_success import TestInitMigration, TestMigration, Test2Migration
from tests.migrations.migrations_classes_fail import HealthyLastMigration, FailTestInitMigration


def test_dataall_full_upgrade_success():
    current_key = TestInitMigration.revision_id()
    manager = MigrationManager(current_key, TestInitMigration)
    new_version = manager.upgrade()
    assert new_version == Test2Migration.revision_id()


def test_dataall_partial_upgrade_success():
    current_key = TestInitMigration.revision_id()
    manager = MigrationManager(current_key, TestInitMigration)
    new_version = manager.upgrade(TestMigration.revision_id())
    assert new_version == TestMigration.revision_id()


def test_dataall_full_downrade_success():
    current_key = Test2Migration.revision_id()
    manager = MigrationManager(current_key, TestInitMigration)
    new_version = manager.downgrade()
    assert new_version == TestInitMigration.revision_id()


def test_dataall_partial_downrade_success():
    current_key = Test2Migration.revision_id()
    manager = MigrationManager(current_key, TestInitMigration)
    new_version = manager.downgrade(TestMigration.revision_id())
    assert new_version == TestMigration.revision_id()


def test_incorrect_current_revison_key():
    current_revision = 'incorrect'
    try:
        manager = MigrationManager(current_revision, TestInitMigration)
    except Exception as e:
        assert f'{e}' == f'Revision {current_revision} is not found.'


def test_incorrect_upgrade_revison_key():
    target = 'incorrect'
    try:
        manager = MigrationManager('0', TestInitMigration)
        new_version = manager.upgrade(target)
    except Exception as e:
        assert f'{e}' == f'Failed to find {target}.'


def test_incorrect_downgrade_revison_key():
    target = 'incorrect'
    try:
        manager = MigrationManager('0', TestInitMigration)
        new_version = manager.downgrade(target)
    except Exception as e:
        assert f'{e}' == f'Failed to find {target} in migration history.'


def test_update_rollback():
    manager = MigrationManager('0', FailTestInitMigration)
    new_revision = manager.upgrade()
    assert not new_revision
    assert manager.current_migration.revision_id() == FailTestInitMigration.revision_id()


def test_downgrade_rollback():
    manager = MigrationManager(HealthyLastMigration.revision_id(), FailTestInitMigration)
    new_revision = manager.downgrade()
    assert not new_revision
    assert manager.current_migration.revision_id() == HealthyLastMigration.revision_id()
