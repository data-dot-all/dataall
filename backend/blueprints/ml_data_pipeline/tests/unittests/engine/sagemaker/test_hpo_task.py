from aws_cdk import core
from engine.sagemaker import hpo_task
import yaml


class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            "CDK_DEFAULT_ACCOUNT": "012345678912",
            "CDK_DEFAULT_REGION": "eu-west-1",
        }
        self.pipeline_iam_role_arn = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.ecr_repository_uri = "dkr.012345678912.eu-west-1"
        self.layer_versions = {}
        self.pipeline_name = "pl"
        self.pipeline_region = "eu-west-1"
        self.stage = "test"
        self.resource_tags = {"tag1": "tag1_value"}
        self.tags_tracker = {}

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass


def test_make_hpo_task():
    hpo_config = """
        name: Training
        type: sagemaker_hpo

        ext_job_name: "$.model_name"
        config:
          resources:
              - name: sagemaker_hpo
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
                volume_size: 30
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 2
              max_parallel_training_jobs: 2

          parameter_ranges:
              - name: "alpha"
                min_value: 0
                max_value: 100
                scaling_type: Auto
                type: continuous

              - name: "gamma"
                min_value : 0
                max_value: 5
                scaling_type: Auto
                type: continuous

              - name: "max_delta_step"
                min_value: 1
                max_value: 10
                scaling_type: Auto
                type: integer
              - name: "num_round"
                min_value: 10
                max_value: 30
                type: integer

              - name: "max_depth"
                min_value: 4
                max_value: 8
                type : integer

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
              name: xgboost
              version: "1.2-1"

          output_path_from_input : "$.training_output"

          training_input_from_path:
              content_type: "$.training_input.content_type"
              train_s3_uri :
                 bucket: "$.training_input.train_s3_bucket"
                 prefix_key: "$.training_input.train_s3_prefix_key"
              validation_s3_uri:
                 bucket: "$.training_input.validation_s3_bucket"
                 prefix_key: "$.training_input.validation_s3_prefix_key"
              test_s3_uri:
                 bucket: "$.training_input.test_s3_bucket"
                 prefix_key: "$.training_input.test_s3_prefix_key"

          resource_ref: sagemaker_hpo

          max_runtime: 400000

        retry:
           retry_attempt: 3

        hpo_result_path : "$.hpo_output"

        model:
          model_name_path: "$.model_name"

    """
    config = yaml.safe_load(hpo_config)

    stack = ATestStack()
    definition = hpo_task.definition_from_config(stack, config, "hpo_path", 1, 2)
    print(definition)
    hpt_job_config_definition = definition.get("Parameters").get("HyperParameterTuningJobConfig")
    assert hpt_job_config_definition.get("Strategy") == "Bayesian"
    assert hpt_job_config_definition.get("HyperParameterTuningJobObjective") == {
        "Type": "Minimize",
        "MetricName": "validation:merror",
    }
    assert hpt_job_config_definition.get("ResourceLimits") == {
        "MaxNumberOfTrainingJobs": 2,
        "MaxParallelTrainingJobs": 2,
    }
    assert hpt_job_config_definition.get("ParameterRanges") == {
        "ContinuousParameterRanges": [
            {"Name": "alpha", "MinValue": "0", "MaxValue": "100", "ScalingType": "Auto"},
            {"Name": "gamma", "MinValue": "0", "MaxValue": "5", "ScalingType": "Auto"},
        ],
        "IntegerParameterRanges": [
            {"Name": "max_delta_step", "MinValue": "1", "MaxValue": "10", "ScalingType": "Auto"},
            {"Name": "num_round", "MinValue": "10", "MaxValue": "30", "ScalingType": "Auto"},
            {"Name": "max_depth", "MinValue": "4", "MaxValue": "8", "ScalingType": "Auto"},
        ],
    }

    training_job_definition = definition.get("Parameters").get("TrainingJobDefinition")

    assert training_job_definition.get("AlgorithmSpecification")
    assert [channel.get("ChannelName") for channel in training_job_definition.get("InputDataConfig")] == [
        "train",
        "validation",
        "test",
    ]
    assert training_job_definition.get("StoppingCondition").get("MaxRuntimeInSeconds") == 400000

    assert training_job_definition.get("ResourceConfig") == {
        "InstanceCount": 1,
        "InstanceType": "ml.m5.2xlarge",
        "VolumeSizeInGB": 30,
    }
    assert training_job_definition.get("StaticHyperParameters").get("num_class") == "3"

    train_channel = training_job_definition.get("InputDataConfig")[0]
    validation_channel = training_job_definition.get("InputDataConfig")[1]
    test_channel = training_job_definition.get("InputDataConfig")[2]

    assert "training_input.train_s3_bucket" in train_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )
    assert "training_input.train_s3_prefix_key" in train_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )

    assert "training_input.validation_s3_bucket" in validation_channel.get("DataSource").get(
        "S3DataSource"
    ).get("S3Uri.$")
    assert "training_input.validation_s3_prefix_key" in validation_channel.get("DataSource").get(
        "S3DataSource"
    ).get("S3Uri.$")

    assert "training_input.test_s3_bucket" in test_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )
    assert "training_input.test_s3_prefix_key" in test_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )


def test_make_hpo_task_input_from_path():
    "Instead of training_input_from_math, the full input_data_config comes from step function input" ""
    hpo_config = """
        name: Training
        type: sagemaker_hpo

        config:
          resources:
              - name: sagemaker_hpo
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
                volume_size: 30
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 2
              max_parallel_training_jobs: 2

          parameter_ranges:
              - name: "num_round"
                min_value: 10
                max_value: 30
                type: integer

              - name: "max_depth"
                min_value: 4
                max_value: 8
                type : integer

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
              name: xgboost
              version: "1.2-1"

          output_path_from_input : "$.training_output"

          input_paths_from_input: "$.trainig_input"
          resource_ref: sagemaker_hpo
    """
    stack = ATestStack()
    config = yaml.safe_load(hpo_config)
    definition = hpo_task.definition_from_config(stack, config, "hpo_path", 1, 2)

    training_job_definition = definition.get("Parameters").get("TrainingJobDefinition")

    assert training_job_definition.get("InputDataConfig.$")


def test_make_hpo_task_hardcoded_input():
    hpo_config = """
        name: Training
        type: sagemaker_hpo

        config:
          resources:
              - name: sagemaker_hpo
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
                volume_size: 30
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 2
              max_parallel_training_jobs: 2

          parameter_ranges:
              - name: "alpha"
                min_value: 0
                max_value: 2
                type: continuous

              - name: "tree_method"
                type: category
                values:
                    - hist
                    - exact

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
              name: xgboost
              version: "1.2-1"

          output_path_from_input : "$.training_output"

          input_data:
              bucket: dhirisymsndfk
              content_type: "text/csv"
              
              training_data:
                prefix_key: "prepared/iris/train.csv"
              validation_data:
                 prefix_key: "prepared/iris/validation.csv"

          resource_ref: sagemaker_hpo
   """
    stack = ATestStack()
    config = yaml.safe_load(hpo_config)
    definition = hpo_task.definition_from_config(stack, config, "hpo_path", 1, 2)

    training_job_definition = definition.get("Parameters").get("TrainingJobDefinition")

    train_channel = training_job_definition.get("InputDataConfig")[0]
    validation_channel = training_job_definition.get("InputDataConfig")[1]

    assert train_channel["ChannelName"] == "train"
    assert train_channel["ContentType"] == "text/csv"
    assert (
        train_channel["DataSource"]["S3DataSource"]["S3Uri"] == "s3://dhirisymsndfk/prepared/iris/train.csv"
    )
    assert (
        validation_channel["DataSource"]["S3DataSource"]["S3Uri"]
        == "s3://dhirisymsndfk/prepared/iris/validation.csv"
    )


def test_make_hpo_task_train_test_novalidation():
    hpo_config = """
        name: Training
        type: sagemaker_hpo

        config:
          resources:
              - name: sagemaker_hpo
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
                volume_size: 30
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 2
              max_parallel_training_jobs: 2

          parameter_ranges:
              - name: "num_round"
                min_value: 10
                max_value: 30
                type: integer

              - name: "max_depth"
                min_value: 4
                max_value: 8
                type : integer

              - name: "tree_method"
                type: category
                values:
                    - hist
                    - exact

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
             name: xgboost
             version: "1.2-1"

          output_data_path:
            bucket: dhirisymsndfk
            prefix_key: training_output

          input_data:
              bucket: dhirisymsndfk
              content_type: "text/csv"
              
              training_data:
                prefix_key: "prepared/iris/train.csv"
              test_data:
                 prefix_key: "prepared/iris/test.csv"

          resource_ref: sagemaker_hpo"""
    stack = ATestStack()
    config = yaml.safe_load(hpo_config)
    definition = hpo_task.definition_from_config(stack, config, "hpo_path", 1, 2)

    training_job_definition = definition.get("Parameters").get("TrainingJobDefinition")

    train_channel = training_job_definition.get("InputDataConfig")[0]
    test_channel = training_job_definition.get("InputDataConfig")[1]

    assert (
        train_channel["DataSource"]["S3DataSource"]["S3Uri"] == "s3://dhirisymsndfk/prepared/iris/train.csv"
    )
    assert test_channel["DataSource"]["S3DataSource"]["S3Uri"] == "s3://dhirisymsndfk/prepared/iris/test.csv"
    assert training_job_definition["OutputDataConfig"]["S3OutputPath"] == "s3://dhirisymsndfk/training_output"


def test_make_hpo_task_train_and_test_from_ref():
    hpo_config = """
        name: Training
        type: sagemaker_hpo

        ext_job_name: "$.model_name"
        config:
          resources:
              - name: sagemaker_hpo
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 2
              max_parallel_training_jobs: 2

          parameter_ranges:

              - name: "max_delta_step"
                min_value: 1
                max_value: 10
                scaling_type: Auto
                type: integer
              - name: "num_round"
                min_value: 10
                max_value: 30
                type: integer

              - name: "max_depth"
                min_value: 4
                max_value: 8
                type : integer

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
              name: xgboost
              version: "1.2-1"

          output_path_from_input : "$.training_output"

          training_input_from_path:
              content_type: "$.training_input.content_type"
              train_s3_uri :
                 bucket: "$.training_input.train_s3_bucket"
                 prefix_key: "$.training_input.train_s3_prefix_key"
              test_s3_uri:
                 bucket: "$.training_input.test_s3_bucket"
                 prefix_key: "$.training_input.test_s3_prefix_key"

          resource_ref: sagemaker_hpo

          max_runtime: 400000

        retry:
           retry_attempt: 3

        hpo_result_path : "$.hpo_output"

        model:
          model_name_path: "$.model_name"
   """
    stack = ATestStack()
    config = yaml.safe_load(hpo_config)
    definition = hpo_task.definition_from_config(stack, config, "hpo_path", 1, 2)

    training_job_definition = definition.get("Parameters").get("TrainingJobDefinition")

    train_channel = training_job_definition.get("InputDataConfig")[0]
    test_channel = training_job_definition.get("InputDataConfig")[1]

    assert len(training_job_definition.get("InputDataConfig")) == 2

    assert "training_input.train_s3_bucket" in train_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )
    assert "training_input.train_s3_prefix_key" in train_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )

    assert "training_input.test_s3_bucket" in test_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )
    assert "training_input.test_s3_prefix_key" in test_channel.get("DataSource").get("S3DataSource").get(
        "S3Uri.$"
    )


def test_make_hpo_task_invalid_parameter():
    hpo_config = """
        name: Training
        type: sagemaker_hpo

        ext_job_name: "$.model_name"
        config:
          resources:
              - name: sagemaker_hpo
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
                volume_size: 5
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 2
              max_parallel_training_jobs: 2

          parameter_ranges:
              - name: "alpha"
                min_value: 0
                max_value: 100
                scaling_type: Auto
                type: continuous

              - name: "gamma"
                min_value : 0
                max_value: 5
                scaling_type: Auto
                type: continuous
              
              - name: "tree_method"
                type: string
                values:
                    - hist
                    - exact

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
              training_image: "141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-xgboost:1.2-1"

          output_path_from_input : "$.training_output"

          training_input_from_path:
              content_type: "$.training_input.content_type"              
              train_s3_uri :
                 bucket: "$.training_input.train_s3_bucket"
                 prefix_key: "$.training_input.train_s3_prefix_key"
              test_s3_uri:
                 bucket: "$.training_input.test_s3_bucket"
                 prefix_key: "$.training_input.test_s3_prefix_key"

          resource_ref: sagemaker_hpo

          max_runtime: 400000

          retry:
             retry_attempt: 3

          hpo_result_path : "$.hpo_output"

          model:
             model_name_path: "$.model_name"
   """
    stack = ATestStack()
    config = yaml.safe_load(hpo_config)

    invalid_type = False
    try:
        definition = hpo_task.definition_from_config(stack, config, "hpo_path", 1, 2)
    except:
        invalid_type = True

    assert invalid_type
