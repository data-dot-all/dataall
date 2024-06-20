from migrations.dataall_migrations.base_migration import BaseDataAllMigration


class RemoveWildCard(BaseDataAllMigration):
    key = '51132fed-c36d-470c-9946-5164581856cb'
    name = 'Remove Wildcard from Sharing Policy'
    description = 'Remove Wildcard from Sharing Policy'

    previous_migration = '0'

    @classmethod
    def up(cls):
        print('up')
