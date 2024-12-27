from . import core, version
from .base import utils, db, api
import logging
import os
import sys

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    handlers=[logging.StreamHandler(sys.stdout)],
    format='[%(levelname)s] %(message)s',
)
for name in ['boto3', 's3transfer', 'botocore', 'boto', 'urllib3']:
    logging.getLogger(name).setLevel(logging.ERROR)
