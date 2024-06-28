import logging
import os
from migrations.dataall_migrations.herder import Herder

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def handler(event, context) -> None:
    H = Herder()
    H.upgrade()


