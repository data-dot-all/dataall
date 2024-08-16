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
    event_command = event.get('command', 'upgrade')
    event_args = event.get('args', {'revision': 'head'})
    logger.info(f'calling alembic "{event_command}({event_args})"')
    getattr(command, event_command)(config=alembic_cfg, **event_args)
