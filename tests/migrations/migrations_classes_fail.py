from migrations.dataall_migrations.base_migration import MigrationBase
from typing import Type, Union


class HealthyLastMigration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '4'

    @classmethod
    def description(cls) -> str:
        return 'HealthyLastMigration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return None

    @classmethod
    def up(cls) -> None:
        print('HealthyLastMigration.Up')

    @classmethod
    def down(cls) -> None:
        print('HealthyLastMigration. Down')


class FailTestBADMigration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '3'

    @classmethod
    def description(cls) -> str:
        return 'FailTest BAD migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return HealthyLastMigration

    @classmethod
    def up(cls) -> None:
        print('FAIL UP.')
        raise Exception('FAIL UP')

    @classmethod
    def down(cls) -> None:
        print('FAIL DOWN.')
        raise Exception('FAIL DOWN')


class FailTest2Migration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '2'

    @classmethod
    def description(cls) -> str:
        return 'FailTest 2 migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return FailTestBADMigration

    @classmethod
    def up(cls) -> None:
        print('FailTest 2 migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('FailTest 2 migration. Down')


class FailTestMigration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '1'

    @classmethod
    def description(cls) -> str:
        return 'FailTest 1 migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return FailTest2Migration

    @classmethod
    def up(cls) -> None:
        print('FailTest1 migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('FailTest1 migration. Down')


class FailTestInitMigration:
    @classmethod
    def revision_id(cls) -> str:
        return '0'

    @classmethod
    def description(cls) -> str:
        return 'Initial migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return FailTestMigration

    @classmethod
    def up(cls) -> None:
        print('Initial test migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('Initial test migration. Down')
