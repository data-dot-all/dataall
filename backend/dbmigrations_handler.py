"""
The handler of this module will be called once upon every deployment
"""

from alembic import command
from alembic.config import Config


def handler(event, context) -> None:
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option('script_location', './migrations')
    command.upgrade(alembic_cfg, 'head')  # logging breaks after this command
