import os

from utils.task_group_reader import TaskGroupReader


def test_nominal():
    """ Test the basic case where the parser goes fine."""
    pipeline = TaskGroupReader(path="tests/unittests/config_files/config_nominal.yaml")
    assert len(pipeline.definition.get("groups")) == 2
    assert len(pipeline.definition.get("aws_resources")) == 4
    assert pipeline.definition.get("name") == "Irispipeline"


def test_template():
    """ Test with basic template"""
    os.environ["STAGE"] = "DEV"
    os.environ["BUCKET_NAME"] = "irisclassification-bucket"
    os.environ["ENVROLEARN"] = "arn:aws:iam::0123456789012:role/dhdatasciencedevoqtnpj"

    pipeline = TaskGroupReader(path="tests/unittests/config_files/config_with_template.yaml")

    assert pipeline.definition.get("name") == "Irispipeline"
    assert (
        pipeline.definition.get("groups")[0].get("jobs")[0].get("description")
        == "Preparing training and test data for iris dataset at the bucket irisclassification-bucket."
    )


def test_template_with_vars():
    """ Tests parsing with templating with variables given from the input. """
    pipeline = TaskGroupReader(
        path="tests/unittests/config_files/config_with_template.yaml",
        template_vars={"stage": "Test", "pipeline_bucket": "irisclassification"},
    )

    assert pipeline.definition.get("name") == "Irispipeline"
    assert (
        pipeline.definition.get("groups")[0].get("jobs")[0].get("description")
        == "Preparing training and test data for iris dataset at the bucket irisclassification."
    )

def test_wrong_parameters():
    parameter_problems = False
    try:
        pipeline = TaskGroupReader(config=None, path=None)
    except :
        parameter_problems = True
    assert parameter_problems


def test_template_from_string():
    """ Tests template from configuration given in a string, instead of file."""
    config = """
name : Irispipeline
comment: Iris pipeline from preparation to deployment
aws_resources:

  - name: datascience_layer
    type: lambda_layers
    config:
       layer_entry: lambda_layers/pandas_sklearn
       bundle_type: custom
       cmd: "rm -rf /asset-output/python  && pip install -r requirements.txt --target /asset-output/python --quiet &&  rm -rf /asset-output/python/scipy* && rm -rf /asset-output/python/numpy*"

  - name: numpy_scipy37
    type: lambda_layers
    config:
        layer_arn:
                arn: "arn:aws:lambdafx:eu-west-1:399891621064:layer:AWSLambda-Python37-SciPy1x:37"
                id: "scipynumpy"
groups:

  - name: "Prepare iris data"
    glue_jobs:
      - name: prepare_function
        description: "Preparing training and test data for iris dataset at the bucket."
        type: lambda_function
        config:
          entry: "lambda_functions/prepare_iris"
          layer_ref:
             - datascience_layer
             - numpy_scipy37
          timeout: 300
"""
    pipeline = TaskGroupReader(config=config)
    assert len(pipeline.definition.get("groups")) == 1
    assert len(pipeline.definition.get("aws_resources")) == 2
    assert pipeline.definition.get("name") == "Irispipeline"


