# This  module is a very simple REST API that uses FastAPI and uvicorn
# it exposes 4 APIs at following paths:
# GET / : returns 200 to notify the server is up
# POST /stack/{stackid} : deploys or updates the stack as found in the dataall database in the stack table
# GET /stack/{stackid} : returns metadata for the stack
# DELETE /Stack/{stackid} : deletes the stack
# To run the server locally, simply run
# uvicorn dataall.base.cdkproxy.main:app --host 0.0.0.0 --port 8080
# To run in docker, build the image and run the container as described in dataall/base/cdkproxy/README.md

import logging
import os
import sys
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, BackgroundTasks, status, Response

import cdk_cli_wrapper as wrapper
from stacks import StackManager
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.stacks.db.stack_models import Stack
from dataall.base.db import get_engine

print('\n'.join(sys.path))

logger = logging.getLogger('cdksass')

ENVNAME = os.getenv('envname', 'local')
logger.warning(f'Application started for envname= `{ENVNAME}`')

StackManager.registered_stacks()


def connect():
    logger.info(f'Connecting to database for environment: `{ENVNAME}`')
    try:
        engine = get_engine(envname=ENVNAME)
        with engine.scoped_session() as session:
            orgs = session.query(Organization).all()
        return engine
    except Exception:
        raise Exception('Connection Error')


app = FastAPI()


@app.get('/', status_code=status.HTTP_200_OK)
def up(response: Response):
    logger.info('GET /')
    return {'_ts': datetime.now().isoformat(), 'message': 'Service is up'}


@app.get('/awscreds', status_code=status.HTTP_200_OK)
def check_creds(response: Response):
    logger.info('GET /awscreds')
    try:
        region = os.getenv('AWS_REGION', 'eu-west-1')
        sts = boto3.client('sts', region_name=region, endpoint_url=f'https://sts.{region}.amazonaws.com')
        data = sts.get_caller_identity()
        return {
            '_ts': datetime.now().isoformat(),
            'message': 'Retrieved current credentials',
            'data': {
                'UserId': data.get('UserId'),
                'Account': data.get('Account'),
                'Arn': data.get('Arn'),
            },
        }
    except ClientError as e:
        logger.exception('AWSCREDSERROR')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            '_ts': datetime.now().isoformat(),
            'message': 'Could not retrieve current aws credentials',
            'data': None,
            'error': str(e),
        }


@app.get('/connect', status_code=status.HTTP_200_OK)
def check_connect(response: Response):
    logger.info('GET /connect')
    try:
        engine = connect()
        return {
            '_ts': datetime.now().isoformat(),
            'message': f'Connected to database for environment {ENVNAME}({engine.dbconfig.host})',
        }
    except Exception as e:
        logger.exception('DBCONNECTIONERROR')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            '_ts': datetime.now().isoformat(),
            'error': str(e),
            'message': f'Failed to connect to database for environment `{ENVNAME}`',
        }


@app.get('/cdk-installed', status_code=status.HTTP_200_OK)
def check_cdk_installed(response: Response):
    logger.info('GET /cdk-installed')
    try:
        wrapper.cdk_installed()
        return {
            '_ts': datetime.now().isoformat(),
            'message': 'Successfully ran cdk cli',
        }
    except Exception as e:
        logger.exception('CDKINSTALLERROR')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            '_ts': datetime.now().isoformat(),
            'error': str(e),
            'message': 'Failed to run cdk cli',
        }


@app.post('/stack/{stackid}', status_code=status.HTTP_202_ACCEPTED)
async def create_stack(stackid: str, background_tasks: BackgroundTasks, response: Response):
    """Deploys or updates the stack"""
    logger.info(f'POST /stack/{stackid}')
    try:
        engine = connect()
    except Exception as e:
        print(e)
        logger.exception('DBCONNECTION')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            '_ts': datetime.now().isoformat(),
            'error': str(e),
            'message': f'Failed to connect to database for environment `{ENVNAME}`',
        }

    with engine.scoped_session() as session:
        stack: Stack = session.query(Stack).get(stackid)
        if not stack:
            logger.warning(f'Could not find stack with stackUri `{stackid}`')
            response.status_code = status.HTTP_302_FOUND
            return {
                '_ts': datetime.now().isoformat(),
                'error': 'ObjectNotFound',
                'message': f'Stack {stackid} not found',
            }  # yaml.safe_load(response.stdout)
        stack.status = 'RUNNING'
    logger.info('Adding bg task')
    background_tasks.add_task(wrapper.deploy_cdk_stack, engine, stackid)
    return {
        '_ts': datetime.now().isoformat(),
        'message': f'Starting creation of StackId {stack.stackUri} on Account {stack.accountid} / Region {stack.region}',
    }


@app.delete('/stack/{stackid}', status_code=status.HTTP_202_ACCEPTED)
async def delete_stack(stackid: str, background_tasks: BackgroundTasks, response: Response):
    """
    Deletes the stack
    """
    logger.info(f'DELETE /stack/{stackid}')
    try:
        engine = connect()
    except Exception as e:
        logger.exception('DBCONNECTION')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            '_ts': datetime.now().isoformat(),
            'error': str(e),
            'message': f'Failed to connect to database for environment `{ENVNAME}`',
        }
    with engine.scoped_session() as session:
        stack: Stack = session.query(Stack).get(stackid)
        if not stack:
            logger.warning(f'Could not find stack with stackUri `{stackid}`')
            response.status_code = status.HTTP_302_FOUND
            return {
                '_ts': datetime.now().isoformat(),
                'error': 'ObjectNotFound',
                'message': f'Stack {stackid} not found',
            }
        stack.status = 'DELETING'

    background_tasks.add_task(wrapper.destroy_cdk_stack, engine, stackid)
    return {
        '_ts': datetime.now().isoformat(),
        'message': f'Starting deletion of StackId {stack.stackUri} on Account {stack.accountid} / Region {stack.region}',
    }


@app.get('/stack/{stackid}', status_code=status.HTTP_200_OK)
def get_stack(stackid: str, response: Response):
    """
    Returns {StackId:"", "StackStatus"} for the given stack
    """
    logger.info(f'GET /stack/{stackid}')
    try:
        engine = connect()
    except Exception as e:
        logger.exception('DBCONNECTION')
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            '_ts': datetime.now().isoformat(),
            'error': str(e),
            'message': f'Failed to connect to database for environment `{ENVNAME}`',
        }
    with engine.scoped_session() as session:
        stack: Stack = session.query(Stack).get(stackid)
        if not stack:
            logger.warning(f'Could not find stack with stackUri `{stackid}`')
            response.status_code = status.HTTP_404_NOT_FOUND
            return {
                '_ts': datetime.now().isoformat(),
                'error': 'ObjectNotFound',
                'message': f'Stack {stackid} not found',
            }
        try:
            meta = wrapper.describe_stack(None, engine, stackid)
            return meta
        except Exception:
            response.status_code = status.HTTP_404_NOT_FOUND
