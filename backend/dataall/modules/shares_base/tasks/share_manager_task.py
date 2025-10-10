import logging
import os
import sys

from dataall.modules.shares_base.services.sharing_service import SharingService
from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode

log = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        load_modules(modes={ImportMode.SHARES_TASK})
        ENVNAME = os.environ.get('envname', 'local')
        ENGINE = get_engine(envname=ENVNAME)

        share_uri = os.getenv('shareUri')
        share_item_uri = os.getenv('shareItemUris')
        handler = os.getenv('handler')

        log.info(f'Starting {handler} task for share : {share_uri}...')
        getattr(SharingService, handler)(engine=ENGINE, share_uri=share_uri)

        log.info('Sharing task finished successfully')

    except Exception as e:
        log.error(f'Sharing task failed due to: {e}')
        raise e
