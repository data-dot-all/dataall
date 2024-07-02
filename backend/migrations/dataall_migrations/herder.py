import importlib
import importlib.machinery
import inspect
import os
from pathlib import Path
from migrations.dataall_migrations.base_migration import BaseDataAllMigration

import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class Herder:
    def __init__(self):
        self.current_key = None
        self.migration_path = {}
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.folder_path = os.path.join(dir_path, 'versions')
        self.initial_key = '0'
        self.last_key = None

        logger.info('Loading migrations...')
        logger.info(f'Folder path: {self.folder_path}')

        for py_file in Path(self.folder_path).glob('*.py'):
            module_name = py_file.stem  # Get the module name (file name without extension)
            module_path = str(py_file.absolute())
            # Import the module
            loader = importlib.machinery.SourceFileLoader(module_name, module_path)
            module = loader.load_module()
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if obj is a subclass of MyClass and not MyClass itself
                if issubclass(obj, BaseDataAllMigration) and obj is not BaseDataAllMigration:
                    self.migration_path[obj.key()] = obj

        for key, migration in self.migration_path.items():
            prev = migration.previous_migration()
            if prev is not None:
                self.migration_path[prev].set_next(key)

        for key, migration in self.migration_path.items():
            if migration.next() is None:
                self.last_key = key
                break

    def upgrade(self, target_key=None, start_key=None, downgrade_if_fails=True):
        if start_key is not None:
            self.current_key = self.migration_path[start_key].next()
            if self.current_key is None:
                logger.info('Data-all version is up to date')
                return
        else:
            self.current_key = self.initial_key
        logger.info(f"Upgrade from {self.current_key} to {target_key if target_key is not None else 'latest'}")
        while self.current_key is not None:
            migration = self.migration_path[self.current_key]
            try:
                logger.info(f'Applying migration {migration.name()}')
                migration.up()
                logger.info(f'Migration {migration.name()} completed')
            except Exception as e:
                logger.info(f'An error occurred while applying the migration.{e}.')
                self.current_key = migration.previous_migration()
                logger.info(f'Upgrade terminated. Current revision is {self.current_key}')
                if downgrade_if_fails:
                    self.downgrade(start_key, self.current_key, False)
                return False
            if self.current_key == target_key:
                break
            self.current_key = migration.next()
        logger.info('Upgrade completed')
        return True

    def downgrade(self, target_key=None, start_key=None, upgrade_if_fails=True):
        self.current_key = start_key if start_key is not None else self.last_key
        logger.info(
            f"Downgrade from {start_key if start_key is not None else 'latest'} to {target_key if target_key is not None else 'initial'}"
        )
        while self.current_key != '0':
            migration = self.migration_path[self.current_key]
            try:
                logger.info(f'Reverting migration {migration.name()}')
                migration.down()
                logger.info(f'Migration {migration.name()} completed')
            except Exception as e:
                logger.info(f'An error occurred while reverting the migration.{e}.')
                logger.info(f'Downgrade terminated. Current revision is {self.current_key}')
                if upgrade_if_fails:
                    self.upgrade(start_key, self.current_key, False)
                return False
            if self.current_key == target_key:
                break
            self.current_key = migration.previous_migration()
        logger.info('Downgrade completed')
        return True
