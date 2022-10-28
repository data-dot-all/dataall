import logging
import os
import sys

from ..cdkproxy.cdk_cli_wrapper import deploy_cdk_stack
from ..db import get_engine

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    envname = os.environ.get('envname', 'local')
    engine = get_engine(envname=envname)

    stack_uri = os.getenv('stackUri')
    logger.info(f'Starting deployment task for stack : {stack_uri}')

    deploy_cdk_stack(engine=engine, stackid=stack_uri, app_path='../cdkproxy/app.py')

    logger.info('Deployment task finished successfully')
