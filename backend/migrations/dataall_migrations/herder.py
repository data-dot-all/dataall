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
                    self.migration_path[obj.key] = obj

        for key, migration in self.migration_path.items():
            prev = migration.previous()
            if prev is not None:
                self.migration_path[prev].set_next(key)

        for key, migration in self.migration_path.items():
            if migration.next() is None:
                self.last_key = key
                break

    def upgrade(self, target_key=None, start_key=None):
        if start_key is not None:
            key = self.migration_path[start_key].next()
            if key is None:
                logger.info('Data-all version is up to date')
                return
        else:
            key = self.initial_key
        logger.info(f"Upgrade from {key} to {target_key if target_key is not None else 'latest'}")
        while key is not None:
            migration = self.migration_path[key]
            logger.info(f'Applying migration {migration.name}')
            migration.up()
            logger.info(f'Migration {migration.name} completed')
            if key == target_key:
                break
            key = migration.next()
        logger.info('Upgrade completed')

    def downgrade(self, target_key=None, start_key=None):
        key = start_key if start_key is not None else self.last_key
        logger.info(
            f"Downgrade from {start_key if start_key is not None else 'latest'} to {target_key if target_key is not None else 'initial'}"
        )
        while key != '0':
            migration = self.migration_path[key]
            logger.info(f'Reverting migration {migration.name}')
            migration.down()
            logger.info(f'Migration {migration.name} completed')
            if key == target_key:
                break
            key = migration.previous()

        logger.info('Downgrade completed')
