from aws_cdk import core

from engine import SageMakerTrainingJobPropsMapper
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
        self.pipeline_region = 'eu-west-1'
        self.resource_tags = {}


config = """
name : unbeliebable
variables:
  dev:
    foo : bar
  prod:
    foo: foo

groups:
  - name: "Train"
    glue_jobs:
      - name: usecasetraining
        type: training
        main: sagemaker_jobs/training/training_job.py
        timeout: 8200
        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
            input_data:
              bucket : sagemaker-eu-west-1-12345678901
              training_data:
                  prefix_key: "data"
            output_data_path:
                bucket: "sagemaker-eu-west-1-12345678901"
                key_prefix: "data"
            hyperparameters:
              p1: "3.8"
              p2: "E"

            resources:
              - name: training_resource
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35

            resource_ref: training_resource

            max_runtime: 3600
            role: "arn:aws:iam::12345678901:role/dataallPivotRole"

"""


def test_map_props():
    training_job = None
    groups = TaskGroupReader(config=config)

    for group in groups.definition.get('groups', []):
        for j in group.get('glue_jobs', []):
            training_job = j

    assert training_job
    assert training_job.get('type') == 'training'
    stack = ATestStack()
    training_props = SageMakerTrainingJobPropsMapper.map_props(
        stack, training_job.get('name'), {}, training_job.get('config'), {}, {}
    )
    print('TPPPPP', training_props)
    assert training_props['OutputDataConfig']
    assert training_props['InputDataConfig']
    assert training_props['HyperParameters']
    assert training_props['StoppingCondition']
    assert training_props['RoleArn']
    assert training_props['AlgorithmSpecification']
    assert training_props['TrainingJobName.$']
