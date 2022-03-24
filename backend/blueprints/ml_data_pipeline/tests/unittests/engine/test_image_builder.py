from engine import SageMakerImageBuilder
from utils.task_group_reader import TaskGroupReader

config = """
name : unbeliebable
variables:
  dev:
    foo : bar
  prod:
    foo: foo

groups:
  - name: "Train"
    jobs:
      - name: usecasetraining
        type: sagemaker_training
        main: tests/customcode/sagemaker_jobs/smjobs/training/training_job.py
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

"""


def test_image_builder(mocker):
    groups = TaskGroupReader(config=config)
    mocker.patch('engine.SageMakerImageBuilder.get_groups', return_value=groups)
    mocker.patch('engine.SageMakerImageBuilder.connect_to_ecr', return_value=True)
    mocker.patch('engine.SageMakerImageBuilder.push_image_to_ecr', return_value=True)
    mocker.patch('engine.SageMakerImageBuilder.build_image_tag', return_value=True)

    image_uris = SageMakerImageBuilder.build_training_jobs_images(
        '12345678901.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job',
        'eu-west-1',
    )

    assert len(image_uris) == 1
