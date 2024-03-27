import logging
import os

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger(__name__)


def ns2d(**kwargs):
    return kwargs


class ParameterStoreManager:
    def __init__(self):
        pass

    @staticmethod
    def client(AwsAccountId=None, region=None, role=None):
        if AwsAccountId:
            log.info(f"SSM Parameter remote session with role:{role if role else 'PivotRole'}")
            session = SessionHelper.remote_session(accountid=AwsAccountId, role=role)
        else:
            log.info('SSM Parameter session in central account')
            session = SessionHelper.get_session()
        return session.client('ssm', region_name=region)

    @staticmethod
    def get_parameter_value(AwsAccountId=None, region=None, parameter_path=None):
        if not parameter_path:
            raise Exception('Parameter name is None')
        try:
            parameter_value = ParameterStoreManager.client(AwsAccountId, region).get_parameter(Name=parameter_path)[
                'Parameter'
            ]['Value']
        except ClientError as e:
            raise Exception(e)
        return parameter_value

    @staticmethod
    def update_parameter(AwsAccountId, region, parameter_name, parameter_value):
        if not parameter_name:
            raise Exception('Parameter name is None')
        if not parameter_value:
            raise Exception('Parameter value is None')
        try:
            response = ParameterStoreManager.client(AwsAccountId, region).put_parameter(
                Name=parameter_name, Value=parameter_value, Overwrite=True
            )['Version']
        except ClientError as e:
            raise Exception(e)
        else:
            return str(response)

    @staticmethod
    def get_pivot_role_as_part_of_environment():
        ssm_param = ParameterStoreManager.get_parameter_value(
            region=os.getenv('AWS_REGION', 'eu-west-1'),
            parameter_path=f"/dataall/{os.getenv('envname', 'local')}/pivotRole/enablePivotRoleAutoCreate",
        )
        return ssm_param == 'True'
