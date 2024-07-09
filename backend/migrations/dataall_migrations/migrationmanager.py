import os
from collections import deque
from typing import Deque
from migrations.dataall_migrations.versions.initial import InitMigration
from migrations.dataall_migrations.base_migration import MigrationBase
from typing import Type, Union

import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class MigrationManager:
    def __init__(self, current_revision='0', initial_migration=InitMigration):
        self.initial_migration = initial_migration
        self.previous_migrations: Deque[Union[Type[MigrationBase], None]] = deque()
        self.current_migration = initial_migration

        while True:
            self.previous_migrations.append(self.current_migration)
            if self.current_migration.revision_id() == current_revision:
                break
            self.current_migration = self.current_migration.next_migration()
            if not self.current_migration:
                raise Exception(f'Revision {current_revision} is not found.')

    def _save_upgraded(self, executed_ups: Deque[Union[Type[MigrationBase], None]]):
        while executed_ups:
            self.previous_migrations.append(executed_ups.popleft())

    def _save_downgrades(self, executed_downs: Deque[Union[Type[MigrationBase], None]]):
        while executed_downs:
            try:
                self.previous_migrations.remove(executed_downs.pop())
            except Exception as e:
                ...

    def _check_downgrade_id(self, target_revision_id):
        for pm in self.previous_migrations:
            if pm.revision_id() == target_revision_id:
                return True
        if target_revision_id == self.current_migration.revision_id():
            return False

        raise Exception(f'Failed to find {target_revision_id} in migration history.')

    def _check_upgrade_id(self, target_revision_id):
        if target_revision_id is None:
            if (
                self.current_migration.next_migration() is None
                or self.current_migration.revision_id() == target_revision_id
            ):
                return False
            return True

        revision = self.current_migration.next_migration()
        while revision is not None:
            if revision.revision_id() == target_revision_id:
                return True
            revision = revision.next_migration()

        raise Exception(f'Failed to find {target_revision_id}.')

    def upgrade(self, target_revision_id=None):
        if not self._check_upgrade_id(target_revision_id):
            logger.info('Data-all version is up to date')
            return self.current_migration.revision_id()

        logger.info(f"Upgrade from {self.current_migration.revision_id()} to {target_revision_id or 'latest'}")
        executed_upgrades: Deque[Union[Type[MigrationBase], None]] = deque()
        saved_start_migration = self.current_migration
        self.current_migration = self.current_migration.next_migration()
        while self.current_migration is not None:
            try:
                logger.info(f'Applying migration {self.current_migration.__name__}')
                self.current_migration.up()
                executed_upgrades.append(self.current_migration)
                logger.info(f'Migration {self.current_migration.__name__} completed')
                if (
                    self.current_migration.revision_id() == target_revision_id
                    or self.current_migration.next_migration() is None
                ):
                    break
                self.current_migration = self.current_migration.next_migration()
            except Exception as e:
                # Something went wrong revert
                logger.exception(f'An error occurred while applying the migration.{e}.')
                while executed_upgrades:
                    migration = executed_upgrades.pop()
                    migration.down()
                self.current_migration = saved_start_migration
                return False
        logger.info('Upgrade completed')
        self._save_upgraded(executed_upgrades)
        return self.current_migration.revision_id()

    def downgrade(self, target_revision_id='0'):
        if not self._check_downgrade_id(target_revision_id):
            logger.info(f'Current revision is  {self.current_migration.revision_id()}')
            return

        logger.info(f"Downgrade from {self.current_migration.revision_id()} to {target_revision_id or 'initial'}")
        executed_downgrades: Deque[Union[Type[MigrationBase], None]] = deque()
        while self.current_migration:
            if self.previous_migrations:
                self.current_migration = self.previous_migrations[-1]
                if self.current_migration.revision_id() == target_revision_id:
                    break
                self.previous_migrations.pop()
            else:
                break

            try:
                logger.info(f'Reverting migration {self.current_migration.__name__}')
                self.current_migration.down()
                executed_downgrades.append(self.current_migration)
                logger.info(f'Migration {self.current_migration.__name__} completed')
            except Exception as e:
                logger.exception(f'An error occurred while reverting the migration.{e}.')
                while executed_downgrades:
                    up_migration = executed_downgrades.pop()
                    up_migration.up()
                    self.current_migration = up_migration
                return False

        logger.info('Downgrade completed')
        self._save_downgrades(executed_downgrades)
        return self.current_migration.revision_id()
