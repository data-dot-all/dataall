import logging
import os
import sys

from .data_sharing.data_sharing_service import DataSharingService
from ..db import get_engine

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


if __name__ == '__main__':

    try:
        ENVNAME = os.environ.get('envname', 'local')
        ENGINE = get_engine(envname=ENVNAME)

        log.info('Starting refresh shares task...')
        DataSharingService.refresh_shares(engine=ENGINE)

        log.info('Sharing task finished successfully')

    except Exception as e:
        log.error(f'Sharing task failed due to: {e}')
        raise e
