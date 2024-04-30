"""
The handler of this module will be called once upon every deployment
"""

import logging
import os

from alembic import command
from alembic.config import Config

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def handler(event, context) -> None:
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option('script_location', './migrations')
    command.upgrade(alembic_cfg, 'head')  # logging breaks after this command
