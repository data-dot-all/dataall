import logging
import os
import sys

from dataall.base.cdkproxy.cdk_cli_wrapper import deploy_cdk_stack
from dataall.base.db import get_engine

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    envname = os.environ.get('envname', 'local')
    engine = get_engine(envname=envname)

    stack_uri = os.getenv('stackUri')
    logger.info(f'Starting deployment task for stack : {stack_uri}')

    deploy_cdk_stack(engine=engine, stackid=stack_uri, app_path='../../base/cdkproxy/app.py')

    logger.info('Deployment task finished successfully')
