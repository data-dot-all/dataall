import os
from collections import deque
from typing import Deque
from migrations.dataall_migrations.versions.initial import InitMigration
from migrations.dataall_migrations.base_migration import MigrationBase

import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class MigrationManager:
    def __init__(self, key='0', initial_migration=InitMigration):
        self.current_migration = initial_migration
        self.previous_migrations: Deque[MigrationBase] = deque()
        while self.current_migration.revision_id() != key:
            self.previous_migrations.append(self.current_migration)
            self.current_migration = self.current_migration.next_migration()
        self.executed_upgrades: Deque[MigrationBase] = deque()
        self.executed_downgrades: Deque[MigrationBase] = deque()

    def upgrade(self, target_key=None):
        if self.current_migration.revision_id() == target_key or self.current_migration.next_migration() is None:
            logger.info('Data-all version is up to date')
            return self.current_migration.revision_id()

        logger.info(f"Upgrade from {self.current_migration.revision_id()} to {target_key or 'latest'}")
        while self.current_migration is not None and self.current_migration.revision_id() != target_key:
            try:
                self.executed_upgrades.append(self.current_migration)
                logger.info(f'Applying migration {self.current_migration.__name__}')
                self.current_migration.up()
                logger.info(f'Migration {self.current_migration.__name__} completed')
                self.current_migration = self.current_migration.next_migration()
            except Exception as e:
                # Something went wrong revert
                logger.info(f'An error occurred while applying the migration.{e}.')
                while self.executed_upgrades:
                    migration = self.executed_upgrades.pop()
                    migration.down()
                return False
        logger.info('Upgrade completed')
        return self.executed_upgrades.pop().revision_id()

    def downgrade(self, target_key='0'):
        logger.info(f"Downgrade from {self.current_migration.revision_id()} to {target_key or 'initial'}")
        self.previous_migrations.append(self.current_migration)
        while migration := self.previous_migrations.pop():
            if migration.revision_id() == target_key:
                break
            try:
                self.executed_downgrades.append(migration)
                logger.info(f'Reverting migration {migration.__name__()}')
                migration.down()
                logger.info(f'Migration {migration.__name__()} completed')
            except Exception as e:
                logger.info(f'An error occurred while reverting the migration.{e}.')
                while self.executed_downgrades:
                    up_migration = self.executed_downgrades.pop()
                    up_migration.up()
                return False

        logger.info('Downgrade completed')
        return target_key
