import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def protect(*protected):
    """Returns a metaclass that protects all attributes given as strings"""

    class Protect(type):
        has_base = False

        def __new__(meta, name, bases, attrs):
            if meta.has_base:
                for attribute in attrs:
                    if attribute in protected:
                        raise AttributeError('Overriding of attribute "%s" not allowed.' % attribute)
            meta.has_base = True
            klass = super().__new__(meta, name, bases, attrs)
            return klass

    return Protect


class BaseDataAllMigration(metaclass=protect('set_next', 'set_previous', 'is_initial', 'is_last')):
    key = '-1'
    name = 'Base Migration'
    description = 'Base Migration'

    @classmethod
    def up(cls):
        logger.info(f'Upgrade is not defined for migration {cls.name}')

    @classmethod
    def down(cls):
        logger.info(f'Downgrade is not defined for migration {cls.name}')

    @classmethod
    def set_previous(cls, previous_migration_key):
        cls.previous_migration = previous_migration_key

    @classmethod
    def set_next(cls, next_migration_key):
        cls.next_migration = next_migration_key

    @classmethod
    def next(cls):
        if 'next_migration' in cls.__dict__:
            return cls.next_migration
        return None

    @classmethod
    def previous(cls):
        if 'previous_migration' in cls.__dict__:
            return cls.previous_migration
        return None

    @classmethod
    def is_initial(cls):
        return 'previous_migration' not in cls.__dict__ or cls.previous_migration is None

    @classmethod
    def is_last(cls):
        return 'next_migration' not in cls.__dict__ or cls.next_migration is None
