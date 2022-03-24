from aws_cdk import core

from engine import LambdaFxPropsMapper
from utils.task_group_reader import TaskGroupReader


class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            'CDK_DEFAULT_ACCOUNT': '012345678912',
            'CDK_DEFAULT_REGION': 'eu-west-1',
        }
        self.pipeline_iam_role_arn = 'dataallPivotRole'
        self.ecr_repository_uri = 'dkr.012345678912.eu-west-1'
        self.layer_versions = {}


config = """
name : unbeliebable
variables:
  dev:
    foo : bar
  prod:
    foo: foo

groups:
  - name: "Function"
    jobs:
    - name: Handlerfx
      type: lambda_function
      config:
        entry: "lambdafx/example_fx"
        index: "example_handler.py"
        handler: "handler"
        layer_entry: "lambdafx/example_fx/"
        payload:
          param: "first_param"


"""


def test_map_props(mocker):
    mocker.patch('engine.LambdaFxPropsMapper.map_role', return_value=True)
    mocker.patch('engine.LambdaFxPropsMapper.map_layers', return_value=True)
    lambdafx = None
    groups = TaskGroupReader(config=config)

    for group in groups.definition.get('groups', []):
        for j in group.get('jobs', []):
            if j.get('type') == 'lambda_function':
                lambdafx = j

    assert lambdafx
    assert lambdafx.get('type') == 'lambda_function'
    stack = ATestStack()
    lambdafx_props = LambdaFxPropsMapper.map_function_props(
        stack, 'myfx', lambdafx['config']
    )
    assert lambdafx_props['handler']
    assert lambdafx_props['index']
    assert lambdafx_props['entry']
    assert lambdafx_props['layers']
    assert lambdafx_props['role']


def test_map_function_props_1():
    config_props = {
        'timeout': 1200,
        'entry': 'lambda_func',
        'role': 'arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj',
        'layer_ref': [],
    }
    stack = ATestStack()
    lambdafx_props = LambdaFxPropsMapper.map_function_props(stack, 'myfx', config_props)

    assert lambdafx_props['handler'] == 'handler'
    assert lambdafx_props['timeout'].to_seconds() == 1200
    assert lambdafx_props['index'] == 'lambda_function.py'
    assert lambdafx_props['entry'] != 'lambda_func'
    assert lambdafx_props['entry'].endswith('lambda_func')
    assert (
        lambdafx_props['role'].role_arn
        == 'arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj'
    )
    assert lambdafx_props['layers'] == []


def test_map_function_props_2():
    config_props = {
        'entry': 'lambdafx/lambda_func',
        'index': 'lambda_function',
        'handler': 'event_handler',
        'role': 'arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj',
        'layer_ref': ['sklearn'],
    }
    stack = ATestStack()

    stack.layer_versions['sklearn'] = 'LV'
    lambdafx_props = LambdaFxPropsMapper.map_function_props(stack, 'myfx', config_props)

    assert lambdafx_props['handler'] == 'event_handler'
    assert lambdafx_props['timeout'].to_seconds() == 900
    assert lambdafx_props['index'] == 'lambda_function'
    assert lambdafx_props['entry'].endswith('lambdafx/lambda_func')
    assert (
        lambdafx_props['role'].role_arn
        == 'arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj'
    )
    assert lambdafx_props['layers'] == ['LV']


def test_map_function_props_3():
    config_props = {
        'entry': 'lambdafx/lambda_func',
        'index': 'lambdafx',
        'handler': 'event_handler',
        'role': 'arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj',
        'dead_letter_queue_enabled': False,
    }
    stack = ATestStack()
    lambdafx_props = LambdaFxPropsMapper.map_function_props(stack, 'myfx', config_props)
    assert lambdafx_props['dead_letter_queue_enabled'] == False


def test_map_function_props_4():
    config_props = {
        'entry': 'lambdafx/lambda_func',
        'index': 'lambdafx',
        'handler': 'event_handler',
        'role': 'arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj',
        'dead_letter_queue_enabled': False,
        'layer_ref': ['sklearn'],
    }

    stack = ATestStack()
    failed = False
    try:
        lambdafx_props = LambdaFxPropsMapper.map_function_props(
            stack, 'myfx', config_props
        )
    except Exception as e:
        print(e)
        assert 'sklearn' in e.message
        failed = True

    assert failed
