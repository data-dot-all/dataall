import logging
import os
from migrations.dataall_migrations.herder import Herder
import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

client = boto3.client('ssm')

envname = os.environ.get('ENVNAME', 'local')
PARAM_KEY = (f'/dataall/{envname}/dataall-migration/revision',)


def get_parameter_from_parameter_store():
    try:
        parameter = client.get_parameter(Name=PARAM_KEY, WithDecryption=True)
        return parameter['Parameter']['Value']
    except client.exceptions.ParameterNotFound:
        # Handle the case where the parameter is not found
        print(f"Error: Parameter '{PARAM_KEY}' not found.")
        return None
    except Exception as e:
        # Handle other exceptions
        print(f'Error: {e}')
        return -1


def put_parameter_to_parameter_store(value):
    try:
        client.put_parameter(Name=PARAM_KEY, Value=value, Type='String', Overwrite=True)
    except Exception as e:
        # Handle other exceptions
        print(f'Error: {e}')


def handler(event, context) -> None:
    revision = get_parameter_from_parameter_store()
    if revision == -1:
        logger.error('Failed to retrieve revision from parameter store')
        return
    H = Herder()
    H.upgrade(start_key=revision)
    put_parameter_to_parameter_store(H.last_key)
