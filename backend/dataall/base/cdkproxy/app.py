# !/usr/bin/python
import json
import logging
import sys

from aws_cdk import Environment, App
from tabulate import tabulate

from dataall.base.cdkproxy.stacks import instanciate_stack
from dataall.base.loader import load_modules, ImportMode

print(sys.version)
logger = logging.getLogger('cdkapp process')
logger.setLevel('INFO')

load_modules(modes={ImportMode.CDK})


class CdkRunner:
    @staticmethod
    def create():
        logger.info('Ï')
        app = App()
        # 1. Reading info from context
        # 1.1 Reading account from context
        table = []
        account = app.node.try_get_context('account')
        table.append(['account', account])
        # logger.info(f"   Aws Account : {account}")

        # 1.2 Reading region  from context
        region = app.node.try_get_context('region')
        table.append(['region', region])

        # 1.3 Reading stack id   from context
        appid = app.node.try_get_context('appid')
        table.append(['appid', appid])
        # 1.4 Reading stack type  from context
        stack_name = app.node.try_get_context('stack')
        table.append(['stack type', stack_name])

        # 1.4 Reading target uri from context
        target_uri = app.node.try_get_context('target_uri')
        table.append(['target uri', target_uri])

        # 1.6
        _data = app.node.try_get_context('data')
        logger.info(f'   **kwargs: {_data}')
        if _data:
            data = json.loads(_data)
            # logger.info(f"  Kwargs: {_data}")
        else:
            data = {}
            # logger.info(f"  Kwargs: None provided")

        # Creating CDK target environment
        env = Environment(account=account, region=region)

        logger.info('Instanciate Stack from parameters')
        tbl = tabulate(table, headers=['Setting', 'Value'])  # , tablefmt="fancy_grid")
        logger.info(tbl)

        instanciate_stack(stack_name, app, appid, env=env, target_uri=target_uri)
        app.synth()


if __name__ == '__main__':
    CdkRunner.create()
