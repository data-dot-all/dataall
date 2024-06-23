import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class Parameter:
    prefix = 'dataall'

    @classmethod
    def ssm(cls):
        client = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
        return client

    @classmethod
    def get_parameter_name(cls, env, path=''):
        pname = f'/{cls.prefix}/{env}/{path}'
        clean = pname.replace('//', '/')
        return clean

    @classmethod
    def put_parameter(cls, env, path='', value='', description=None):
        pname = cls.get_parameter_name(env, path)
        log.info('writing %s', pname)
        ssm = cls.ssm()
        response = ssm.put_parameter(
            Name=pname,
            Description=str(description),
            Value=str(value) if len(str(value)) else '-',
            Type='String',
            Overwrite=True,
        )
        return Parameter.get_parameter(env, path)

    @classmethod
    def get_parameter(cls, env, path=''):
        pname = cls.get_parameter_name(env, path)
        ssm = cls.ssm()
        try:
            param_value = ssm.get_parameter(Name=pname)
            return param_value['Parameter']['Value']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                log.warning('Parameter `{}` not found for env `{}`, defaulting to None'.format(path, env))
                return None
            else:
                log.error('Error trying to retrieve parameter from SSM')
                raise e

    @classmethod
    def clean_environment(cls, env):
        params = cls.get_parameters(env=env)
        for p in params[env]:
            pname = Parameter.get_parameter_name(env=env, path=p['Name'])
            cls.ssm().delete_parameter(Name=pname)

    @classmethod
    def get_parameters(cls, env, prefix=None):
        pname = cls.get_parameter_name(env, prefix or '')
        ssm = cls.ssm()
        response = {env: []}
        paginator = ssm.get_paginator('get_parameters_by_path')
        operation_parameters = {'Path': pname, 'Recursive': True}
        page_iterator = paginator.paginate(**operation_parameters)
        for page in page_iterator:
            parameters = page['Parameters']
            response[env] += [{'Name': p['Name'].replace(pname, ''), 'Value': p['Value']} for p in parameters]

        return response

    @classmethod
    def load(cls, filename, env='dev'):
        try:
            f = open(filename)
        except Exception:
            raise Exception('Could not load', filename)

        body = '\n'.join(f.readlines())
        config = json.loads(body)

        total = sum([len(config[topic]) for topic in config.keys()])
        done = 1
        log.info('Writing %(total)s `global` parameters in %(env)s Environment' % vars())
        for topic in config.keys():
            for param in config[topic].keys():
                log.info('     %(done)s/%(total)s written' % vars())
                Parameter.put_parameter(env=env, path='/'.join([topic, param]), value=config[topic][param])
                done += 1


if __name__ == '__main__':
    Parameter.get_parameter(env='staging', path='aurora/host')
