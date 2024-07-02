from migrations.dataall_migrations.base_migration import BaseDataAllMigration


class Init(BaseDataAllMigration):
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
    def previous_migration():
        return None

    @staticmethod
    def up():
        print('Initial migration. Up.')

    @staticmethod
    def down():
        print('Initial migration. Down')
