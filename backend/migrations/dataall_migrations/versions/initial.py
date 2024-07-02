from migrations.dataall_migrations.base_migration import BaseDataAllMigration
from migrations.dataall_migrations.versions.remove_wildcard_share_policy import RemoveWildCard


class InitMigration(BaseDataAllMigration):
    @staticmethod
    def key():
        return '0'

    @staticmethod
    def name():
        return 'Initial migration'

    @staticmethod
    def description():
        return 'Initial migration'

    @staticmethod
    def next_migration():
        return RemoveWildCard

    @staticmethod
    def up():
        print('Initial migration. Up.')

    @staticmethod
    def down():
        print('Initial migration. Down')
