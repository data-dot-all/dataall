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

        share_uri = os.getenv('shareUri')
        share_item_uri = os.getenv('shareItemUri')
        handler = os.getenv('handler')

        if handler == 'approve_share':
            log.info(f'Starting processing task for share : {share_uri}...')
            DataSharingService.approve_share(engine=ENGINE, share_uri=share_uri)

        elif handler == 'revoke_share':
            log.info(f'Starting revoking task for share : {share_uri}...')
            DataSharingService.revoke_share(engine=ENGINE, share_uri=share_uri)

        log.info('Sharing task finished successfully')

    except Exception as e:
        log.error(f'Sharing task failed due to: {e}')
        raise e
