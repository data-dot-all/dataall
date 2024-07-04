from migrations.dataall_migrations.base_migration import MigrationBase
from migrations.dataall_migrations.versions.remove_wildcard_share_policy import RemoveWildCard
from typing import Type, Union


class InitMigration(MigrationBase):
    @classmethod
    def revision_id(cls) -> str:
        return '0'

    @classmethod
    def description(cls) -> str:
        return 'Initial migration'

    @classmethod
    def next_migration(cls) -> Union[Type['MigrationBase'], None]:
        return RemoveWildCard

    @classmethod
    def up(cls) -> None:
        print('Initial migration. Up.')

    @classmethod
    def down(cls) -> None:
        print('Initial migration. Down')
