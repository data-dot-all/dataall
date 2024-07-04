from migrations.dataall_migrations.base_migration import MigrationBase
from typing import Type, Union


class Test2Migration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '2'

    @classmethod
    def description(cls) -> str:
        return 'Test 2 migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return None

    @classmethod
    def up(cls) -> None:
        print('Test 2 migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('Test 2 migration. Down')


class TestMigration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '1'

    @classmethod
    def description(cls) -> str:
        return 'Test 1 migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return Test2Migration

    @classmethod
    def up(cls) -> None:
        print('Test1 migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('Test1 migration. Down')


class TestInitMigration:
    @classmethod
    def revision_id(cls) -> str:
        return '0'

    @classmethod
    def description(cls) -> str:
        return 'Initial migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return TestMigration

    @classmethod
    def up(cls) -> None:
        print('Initial test migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('Initial test migration. Down')
