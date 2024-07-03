from migrations.dataall_migrations.base_migration import MigrationBase
from migrations.dataall_migrations.versions.remove_wildcard_share_policy import RemoveWildCard
from typing import Type


class InitMigration(MigrationBase):
    @staticmethod
    def revision_id() -> str:
        return '0'

    @staticmethod
    def description() -> str:
        return 'Initial migration'

    @staticmethod
    def next_migration() -> Type[MigrationBase] | None:
        return RemoveWildCard

    @staticmethod
    def up() -> None:
        print('Initial migration. Up.')

    @staticmethod
    def down() -> None:
        print('Initial migration. Down')
