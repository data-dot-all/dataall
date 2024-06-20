from migrations.dataall_migrations.base_migration import BaseDataAllMigration


class Init(BaseDataAllMigration):
    key = '0'
    name = 'Initial migration'
    description = 'Initial migration'
