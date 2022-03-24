from aws_cdk import core

from engine import (
    SageMakerEndpointConfigPropsMapper,
    SageMakerEndpointPropsMapper,
    SageMakerModelPropsMapper,
)
from utils.task_group_reader import TaskGroupReader


class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            'CDK_DEFAULT_ACCOUNT': '012345678912',
            'CDK_DEFAULT_REGION': 'eu-west-1',
        }
        self.pipeline_iam_role_arn = 'arn:aws:iam::12345678901:role/dataallPivotRole'
        self.ecr_repository_uri = 'dkr.012345678912.eu-west-1'


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
            algorithm_specification:
              metric_definitions:
                - name: "t1"
                  regex: "."
              training_image:
                image_uri: "12345678901.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job"
                training_input_mode: "FILE"
            input_data_config:
              -
                channel_name: "train"
                data_source:
                  s3_data_source:
                    s3_location:
                      bucket: "sagemaker-eu-west-1-12345678901"
                      key_prefix: "data"
            output_data_config:
              s3_output_location:
                bucket: "sagemaker-eu-west-1-12345678901"
                key_prefix: "data"
            hyperparameters:
              p1: "3.8"
              p2: "E"
            resource_config:
              instance_count: 1
              instance_type: "m4.xlarge"
              volume_size: 35
            vpc_config:
                vpc_id: "vpc-0f63e205b5c888858"
                subnets:
                    -
                      "subnet-0ee1e02177e5fbbb8"
            stopping_condition:
              max_runtime: 3600
            role: "arn:aws:iam::12345678901:role/dataallPivotRole"

  - name: "Serve"
    glue_jobs:
      - name: Model
        type: model
        timeout: 8200
        config:
          model_name: "test_model"
          primary_container:
             algorithm:
                image: "12345678901.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job"
             mode: "SINGLE_MODEL"
             model_path: "$.model_path"
          containers:
           - image: "12345678901.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job"
             mode: "SINGLE_MODEL"
             model_path :  "$.model_path"
           - image: "12345678901.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job"
             mode: "SINGLE_MODEL"
             model_path : "$.model_path"

          enable_network_isolation: True
          vpc: vpc-0f63e205b5c888858
          subnets:
            -
              "subnet-0ee1e02177e5fbbb8"
          tags:
              -
               project: project1
               owner: dataall

      - name: EndpointConfig
        type: endpoint_config
        timeout: 8200
        config:
          initial_instance_count: 1
          instance_type: "m5.xlarge"
          model_name: "model-11"
          variant_name: "wind"
          initial_variant_weight: 1
          kms_key: "arn:aws:kms:eu-west-1:1234567891:key/ehauizyeuiayze"
          tags:
              -
               project: project1
               owner: dataall

      - name: Endpoint
        type: endpoint
        timeout: 8200
        config:
          endpoint_config_name: "EndpointConfig"

"""


def test_map_props():
    # mocker.patch("engine.SageMakerModelPropsMapper.map_role", return_value=True)
    model = None
    endpoint_config = None
    endpoint = None
    groups = TaskGroupReader(config=config)

    print('==>', groups.definition.get('jobdir', 'xxx'))
    for group in groups.definition.get('groups', []):
        for j in group.get('glue_jobs', []):
            if j.get('type') == 'model':
                model = j
            elif j.get('type') == 'endpoint_config':
                endpoint_config = j
            elif j.get('type') == 'endpoint':
                endpoint = j

    assert model
    assert model.get('type') == 'model'

    stack = ATestStack()
    model_props = SageMakerModelPropsMapper.map_props(stack, 'mymodel', model['config'])
    assert model_props['primary_container']
    assert model_props['model_name']
    assert model_props['role']

    assert endpoint_config
    assert endpoint_config.get('type') == 'endpoint_config'

    endpoint_config_props = SageMakerEndpointConfigPropsMapper.map_props(
        stack, 'endpoint_config_name', endpoint_config['config'], None
    )
    assert endpoint_config_props['endpoint_config_name']
    assert endpoint_config_props['production_variants']
    assert endpoint_config_props['kms_key']

    assert endpoint
    assert endpoint.get('type') == 'endpoint'

    endpoint_props = SageMakerEndpointPropsMapper.map_props(
        'endpoint', 'endpoint_config', endpoint['config']
    )
    assert endpoint_props['endpoint_config_name']
    assert endpoint_props['endpoint_name']
