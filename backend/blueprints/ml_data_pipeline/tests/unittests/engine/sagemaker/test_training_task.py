from aws_cdk import core
from engine.sagemaker import training_task, hpo_task
import yaml
from aws_cdk import aws_stepfunctions as stepfunctions


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
        self.tags_tracker = {}

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass
    def make_tag_str(slef):
        pass


def test_make_training_task():
    training_config = """
        name: Training
        type: training
        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
            input_data:
              bucket : dhirisdatasetforclassificationbfxkifeuwest1
              content_type: "text/csv"
              training_data:
                  prefix_key: "prepared/training_data.csv"
              validation_data:
                  prefix_key: "prepared/validation_data.csv"
            output_data_path:
                bucket: dhirisdatasetforclassificationbfxkifeuwest1
                key_prefix: output
            hyperparameters:
              num_round: "10"
              max_depth: "6"
            resources:
              - name: "training-resource"
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35
            resource_ref: "training-resource"
        retry:
           retry_attempt: 3
   """
    config = yaml.safe_load(training_config)
    stack = ATestStack()
    definition = training_task.definition_from_config(stack, config, "$.training_path", 1, 2)
    parameters = definition.get("Parameters")
    assert parameters.get("AlgorithmSpecification").get("TrainingImage")
    assert parameters.get("AlgorithmSpecification").get("TrainingInputMode") == "File"
    assert (
        parameters.get("OutputDataConfig").get("S3OutputPath")
        == "s3://dhirisdatasetforclassificationbfxkifeuwest1/output"
    )
    assert parameters.get("StoppingCondition").get("MaxRuntimeInSeconds") == 3600
    assert parameters.get("ResourceConfig") == {
        "InstanceCount": 1,
        "InstanceType": "m4.xlarge",
        "VolumeSizeInGB": 35,
    }
    assert parameters.get("RoleArn") == stack.pipeline_iam_role_arn
    assert parameters.get("HyperParameters") == {"num_round": "10", "max_depth": "6"}
    assert parameters.get("InputDataConfig") == [
        {
            "ChannelName": "train",
            "ContentType": "text/csv",
            "DataSource": {
                "S3DataSource": {
                    "S3DataDistributionType": "FullyReplicated",
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://dhirisdatasetforclassificationbfxkifeuwest1/prepared/training_data.csv",
                }
            },
        },
        {
            "ChannelName": "validation",
            "ContentType": "text/csv",
            "DataSource": {
                "S3DataSource": {
                    "S3DataDistributionType": "FullyReplicated",
                    "S3DataType": "S3Prefix",
                    "S3Uri": "s3://dhirisdatasetforclassificationbfxkifeuwest1/prepared/validation_data.csv",
                }
            },
        },
    ]
    assert parameters.get("TrainingJobName.$")

    assert len(definition.get("Retry")) == 1
    assert definition["Retry"][0] == {'ErrorEquals': ['SageMaker.AmazonSageMakerException'], 
                                        'IntervalSeconds': 1,
                                        'MaxAttempts': 3,
                                        'BackoffRate': 1.1}



def test_make_train_task_input_from_path():
    "Instead of training_input_from_math, the full input_data_config comes from step function input" ""
    train_config = """
        name: Training
        type: training
        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
            input_paths_from_input: "$.training_input"
            output_data_path:
                bucket: dhirisdatasetforclassificationbfxkifeuwest1
                key_prefix: output
            hyperparameters:
              num_round: "10"
              max_depth: "6"
            resources:
              - name: "training-resource"
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35
            resource_ref: "training-resource"
        retry:
           retry_attempt: 3
    """
    stack = ATestStack()
    config = yaml.safe_load(train_config)
    definition = training_task.definition_from_config(stack, config, "hpo_path", 1, 2)

    training_job_definition = definition.get("Parameters")

    assert training_job_definition.get("InputDataConfig.$")


def test_make_training_task_input_from_sfn_path():
   train_config = """
        name: Training
        type: training
        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
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
            output_path_from_input: "$.training_output"
            hyperparameters:
              num_round: "10"
              max_depth: "6"
            resources:
              - name: "training-resource"
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35
            resource_ref: "training-resource"
    """
   stack = ATestStack()
   config = yaml.safe_load(train_config)
   definition = training_task.definition_from_config(stack, config, "train_path", 1, 2)
   parameters = definition.get("Parameters")
   train_channel = parameters.get("InputDataConfig")[0]
   validation_channel = parameters.get("InputDataConfig")[1]
   test_channel = parameters.get("InputDataConfig")[2]

   assert train_channel.get("DataSource").get("S3DataSource").get("S3Uri.$")
   assert validation_channel.get("DataSource").get("S3DataSource").get("S3Uri.$")
   assert test_channel.get("DataSource").get("S3DataSource").get("S3Uri.$")



def test_make_test_task_train_test_novalidation():
    train_config = """
        name: Training
        type: training
        ext_job_name: "$.model_name"

        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
            training_input_from_path:
              content_type: "$.training_input.content_type"
              train_s3_uri :
                 bucket: "$.training_input.train_s3_bucket"
                 prefix_key: "$.training_input.train_s3_prefix_key"
              test_s3_uri:
                 bucket: "$.training_input.test_s3_bucket"
                 prefix_key: "$.training_input.test_s3_prefix_key"
            output_data_path:
                bucket: dhirisdatasetforclassificationbfxkifeuwest1
                key_prefix: output
            hyperparameters:
              num_round: "10"
              max_depth: "6"
            resources:
              - name: "training-resource"
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35
            resource_ref: "training-resource"
    """
    stack = ATestStack()
    config = yaml.safe_load(train_config)
    definition = training_task.definition_from_config(stack, config, "train_path", 1, 2)
    
    parameters = definition.get("Parameters")
    train_channel = parameters.get("InputDataConfig")[0]
    test_channel = parameters.get("InputDataConfig")[1]

    assert test_channel["ChannelName"] == "test"
    assert train_channel["ChannelName"] == "train"
    assert parameters.get('TrainingJobName.$')

def test_make_test_trask_train_validation_notest():
    train_config = """
        name: Training
        type: training
        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
            training_input_from_path:
              content_type: "$.training_input.content_type"
              train_s3_uri :
                 bucket: "$.training_input.train_s3_bucket"
                 prefix_key: "$.training_input.train_s3_prefix_key"
              validation_s3_uri:
                 bucket: "$.training_input.validation_s3_bucket"
                 prefix_key: "$.training_input.validation_s3_prefix_key"
            output_data_path:
                bucket: dhirisdatasetforclassificationbfxkifeuwest1
                key_prefix: output
            hyperparameters:
              num_round: "10"
              max_depth: "6"
            resources:
              - name: "training-resource"
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35
            resource_ref: "training-resource"
    """
    stack = ATestStack()
    config = yaml.safe_load(train_config)
    definition = training_task.definition_from_config(stack, config, "train_path", 1, 2)
    
    parameters = definition.get("Parameters")
    train_channel = parameters.get("InputDataConfig")[0]
    validation_channel = parameters.get("InputDataConfig")[1]

    assert validation_channel["ChannelName"] == "validation"
    assert train_channel["ChannelName"] == "train"

def test_make_test_trask_with_model():
    train_config = """
        name: Training
        type: training
        ext_job_name: "$.model_name"
        config:
            timeout: 3600
            algorithm:
              name: xgboost
              version: "1.2-1"
            training_input_from_path:
              content_type: "$.training_input.content_type"
              train_s3_uri :
                 bucket: "$.training_input.train_s3_bucket"
                 prefix_key: "$.training_input.train_s3_prefix_key"
              validation_s3_uri:
                 bucket: "$.training_input.validation_s3_bucket"
                 prefix_key: "$.training_input.validation_s3_prefix_key"
            output_data_path:
                bucket: dhirisdatasetforclassificationbfxkifeuwest1
                key_prefix: output
            hyperparameters:
              num_round: "10"
              max_depth: "6"
            resources:
              - name: "training-resource"
                instance_count: 1
                instance_type: "m4.xlarge"
                volume_size: 35
            resource_ref: "training-resource"
        model:
          model_name_path: "$.model_name"
    """
    stack = ATestStack()
    config = yaml.safe_load(train_config)
    task = training_task.make_sagemaker_training_task(stack, config,  1, 2)

    assert isinstance(task, stepfunctions.Chain)
