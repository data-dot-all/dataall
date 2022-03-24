import aws_cdk.aws_dynamodb
import aws_cdk.aws_lambda
from aws_cdk import core

from engine.lambdafx.lambda_mapper import LambdaFxMappingException
from stack import DataPipeline
from utils.task_group_reader import TaskGroupReader

import os

os.environ['BUCKET_NAME'] = 'iris-spec'
os.environ['AWSACCOUNTID'] = '012345678901'
os.environ['ECR_REPOSITORY'] = ' '
os.environ['ENVROLEARN'] = 'arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj'
os.environ['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION', 'eu-west-1')


def test_stack():
    """Test nominal stack with 3 resources and 2 groups whose 1 job each"""
    app = core.App()
    pipeline = TaskGroupReader(path='tests/unittests/config_files/config_nominal.yaml')
    stack = DataPipeline(app, 'pipeline', pipeline, description='testpipeline')

    assert len(stack.layer_versions) == 2
    assert isinstance(
        stack.layer_versions.get('datascience_layer'), aws_cdk.aws_lambda.ILayerVersion
    )
    assert isinstance(
        stack.layer_versions.get('numpy_scipy37'), aws_cdk.aws_lambda.ILayerVersion
    )

    assert len(stack.resources) == 5
    assert isinstance(stack.resources.get('cycles_table'), aws_cdk.aws_dynamodb.Table)

    assert stack.state_machine

    start_state = stack.state_machine_definition.start_state
    assert start_state.id == 'Task Execution Id'
    assert len(stack.state_machine_definition.end_states) == 1

    job_name = pipeline.definition.get('groups')[1].get('jobs')[0].get('name')
    assert (
        stack.state_machine_definition.end_states[0].id
        == f'Lambda: Tag Model model-from-{job_name}'
    )


def test_stack_aws_resources_only():
    """Test the case where the definition of configuration file contains only aws resource"""
    app = core.App()
    pipeline = TaskGroupReader(
        path='tests/unittests/config_files/config_resource_only.yaml'
    )
    stack = DataPipeline(app, 'pipeline', pipeline, description='testpipeline')

    assert len(stack.layer_versions) == 2
    assert len(stack.resources) == 3
    assert not stack.state_machine_definition
    assert not stack.state_machine


def test_stack_no_resources():
    """Test the case where the definition of the configuration file contains groups only."""
    app = core.App()
    pipeline = TaskGroupReader(
        path='tests/unittests/config_files/config_no_resource.yaml'
    )
    stack = DataPipeline(app, 'pipeline', pipeline, description='testpipeline')

    assert stack.state_machine_definition
    assert stack.state_machine

    start_state = stack.state_machine_definition.start_state

    assert start_state.id == 'Task Execution Id'
    assert len(stack.state_machine_definition.end_states) == 1

    job_name = pipeline.definition.get('groups')[1].get('jobs')[0].get('name')
    assert (
        stack.state_machine_definition.end_states[0].id
        == f'Lambda: Tag Model model-from-{job_name}'
    )


def test_error_when_layer_not_defined():
    """Tests the case where a lambdafx layer is referenced by a lambdafx, while the layer is not defined in aws_resource block."""
    try:
        app = core.App()
        pipeline = TaskGroupReader(
            path='tests/unittests/config_files/config_resource_err.yaml'
        )

        DataPipeline(app, 'pipeline', pipeline, description='testpipeline')
        assert False
    except LambdaFxMappingException as e:
        assert e.arg_name == 'layers'


def test_training_complete():
    """Tests stack deployment with training task."""
    app = core.App()
    pipeline = TaskGroupReader(
        path='tests/unittests/config_files/config_training_complete.yaml'
    )
    stack = DataPipeline(app, 'pipeline', pipeline, description='testpipeline')
    assert stack.state_machine


def test_api_gateway():
    app = core.App()
    pipeline = TaskGroupReader(
        path='tests/unittests/config_files/config_with_api_gateway.yaml'
    )
    stack = DataPipeline(app, 'pipeline', pipeline, description='testpipeline')
    assert len(stack.resources) == 1


def test_schedule_step_function():
    """Tests schedule step function."""
    app = core.App()
    pipeline = TaskGroupReader(
        path='tests/unittests/config_files/config_with_schedules.yaml'
    )
    stack = DataPipeline(app, 'pipeline', pipeline, description='testpipeline')
    assert len(stack.resources) == 5 and len(stack.schedules) == 1
