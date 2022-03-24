from aws_cdk import core

from engine import SageMakerProcessingJobPropsMapper
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


config = """
name : unbeliebable
variables:
  dev:
    foo : bar
  prod:
    foo: foo

groups:
  - name: "Process"
    glue_jobs:
      - name: Process
        type: processing
        main: "sagemaker_jobs/processing/processing_job.py"
        config:
            timeout: 3600
            environment:
                - name: "t1"
                  regex: "."
            experiment_config:
                experiment_name: test
                trial_component_display_name: "displayname"
                trial_name: trial_name
            network_config:
              enable_intercontainer_traffic_encryption: true
              enable_network_isolation: false
              vpc_config:
                security_groups:
                 - sg1
                   sg2
                subnets:
                 - subnet-1
                   subnet-2
            processing_inputs:
               - input_name: processname
                 s3_input:
                  local_path: localpath
                  compression_type: compress
                  s3_data:
                    distribution_type: type
                    type: idk
                  s3_input_mode: test
                  s3_uri: https://s3.amazon

               - input_name: input2
                 s3_input:
                  local_path: localpath
                  compression_type: compress
                  s3_data:
                    distribution_type: type
                    type: idk
                  s3_input_mode: test
                  s3_uri: https://s3.amazon

            processing_output_config:
              kms_key_id: 28899988
              outputs:
               - output_name: output1
                 s3_output:
                  local_path: localpaht
                  s3_upload_mode: upload_mode
                  s3_uri: https://s3.amazon

               - output_name: output2
                 s3_output:
                  local_path: localpaht
                  s3_upload_mode: upload_mode
                  s3_uri: https://s3.amazon

            processing_resources:
              cluster_config:
                  instance_count: 1
                  instance_type: ml.m4.xlarge
                  volume_size: 35

            stopping_condition:
              max_runtime: 3600
            role: "arn:aws:iam::12345678901:role/dataallPivotRole"

            tags:
              -
               project: project1
               owner: dataall

"""

config_minimal = """
name : unbeliebable
variables:
  dev:
    foo : bar
  prod:
    foo: foo

groups:
 - name: "Process"
   glue_jobs:
      - name : Processing
        type: processing
        main: "sagemaker_jobs/processing/processing_job.py"
        config:
          stopping_condition:
            max_runtime: 3600
"""


def test_map_props_full():
    groups = TaskGroupReader(config=config)
    processing_job = dict()
    print('==>', groups.definition.get('jobdir', 'xxx'))
    for group in groups.definition.get('groups', []):
        for j in group.get('glue_jobs', []):
            processing_job = j

    assert processing_job
    assert processing_job.get('type') == 'processing'
    stack = ATestStack()
    processing_props = SageMakerProcessingJobPropsMapper.map_props(
        stack,
        processing_job.get('name'),
        processing_job.get('main'),
        processing_job.get('config'),
        tags=['tagPath'],
    )
    assert processing_props['AppSpecification']
    assert processing_props['Environment']
    assert processing_props['ExperimentConfig']
    assert processing_props['NetworkConfig']
    assert processing_props['ProcessingInputs']
    assert processing_props['ProcessingJobName.$']
    assert processing_props['ProcessingOutputConfig']
    assert processing_props['ProcessingResources']
    assert processing_props['RoleArn']
    assert processing_props['StoppingCondition']
    assert processing_props['Tags.$']


def test_map_props_minimal():
    groups = TaskGroupReader(config=config_minimal)
    processing_job = dict()
    print('==>', groups.definition.get('jobdir', 'xxx'))
    for group in groups.definition.get('groups', []):
        for j in group.get('glue_jobs', []):
            processing_job = j

    assert processing_job
    assert processing_job.get('type') == 'processing'
    stack = ATestStack()
    processing_props = SageMakerProcessingJobPropsMapper.map_props(
        stack,
        processing_job.get('name'),
        processing_job.get('main'),
        processing_job.get('config'),
        tags=[],
    )
    assert processing_props['AppSpecification']
    assert processing_props['ProcessingJobName.$']
    assert processing_props['ProcessingResources']
    assert processing_props['RoleArn']
    assert processing_props['StoppingCondition']
