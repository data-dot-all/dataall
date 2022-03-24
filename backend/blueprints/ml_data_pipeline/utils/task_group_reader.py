"""
Configuration file (e.g. config_dpc.yaml) parser"
"""

import os
import yaml
from jinja2 import Template
import boto3


class Stages:
    TEST = "test"
    PROD = "prod"
    INT = "int"
    DEV = "dev"

def environment_variable(name):
    return os.environ.get(name)


def listdir(path):
    return os.listdir(path)


def s3_ls(bucket, prefix):
    client = boto3.client("s3")
    paginator = client.get_paginator("list_objects")
    result = paginator.paginate(Bucket=bucket, Delimiter="/", Prefix=prefix + "/")
    prefixes = []
    for prefix in result.search("CommonPrefixes"):
        prefixes.append(prefix.get("Prefix"))
    return prefixes

class TaskGroupReader:
    """ Configuration file (e.g. config.yaml) parser"""

    def __init__(self, path="config.yaml", config: str = None, template_vars=None):
        if config is None and path is None:
            raise Exception("Expecting config or path")
        self.config = config
        self.path = path
        self.definition = self.parse(template_vars)

    def parse_definition(self, variables):
        if not self.config:
            with open(self.path, "r") as f:
                templatized = Template(f.read())
                templatized.globals["ls"] = listdir
                templatized.globals["s3_ls"] = s3_ls
                templatized.globals["env_var"] = environment_variable

                definition = yaml.safe_load(templatized.render(variables))
        else:
            templatized = Template(self.config)
            templatized.globals["ls"] = listdir
            templatized.globals["s3_ls"] = s3_ls
            templatized.globals["env_var"] = environment_variable

            definition = yaml.safe_load(templatized.render(variables))
        return definition

    def parse(self, variables):
        """ Parses the yaml file of the configuration file. adds vars for config """
        if not variables:
            variables = {}
            variables["stage"] = os.environ.get("STAGE", "TEST")
            if "BUCKET_NAME" in os.environ:
                variables["pipeline_bucket"] = os.environ.get("BUCKET_NAME")
            if "ENVROLEARN" in os.environ:
                variables["environment_role_arn"] = os.environ.get("ENVROLEARN")
            if "ORIGIN_PIPELINE_NAME"  in os.environ:
                variables["pipeline_name"] = os.environ.get("ORIGIN_PIPELINE_NAME")
            if "SAML_GROUP" in os.environ:
                variables["saml_group"] = os.environ.get("saml_group")
            if "AWSACCOUNTID" in os.environ:
                variables["aws_account_id"] = os.environ.get("AWSACCOUNTID")
            if "AWSREGION" in os.environ:
                variables["aws_region"] = os.environ.get("AWSREGION")
            if "SNS_TOPIC_ARN" in os.environ:
                variables["sns_topic_arn"] = os.environ.get("SNS_TOPIC_ARN")
            if "BATCH_INSTANCE_ROLE" in os.environ:
                 variables["batch_instance_role"] = os.environ.get("BATCH_INSTANCE_ROLE")
            if "ENVIRONMENT_URI" in os.environ:
                variables["environment_uri"] = os.environ.get("ENVIRONMENT_URI")
            if "PIPELINE_URI" in os.environ:
                variables["pipeline_uri"] = os.environ.get("PIPELINE_URI")
            if "EC2_SPOT_FLEET_ROLE" in os.environ:
                variables["ec2_spot_fleet_role"] = os.environ.get("EC2_SPOT_FLEET_ROLE")
            if "ECR_REPOSITORY" in os.environ:
                variables["ecr_repository"] = os.environ.get("ECR_REPOSITORY")



        definition = self.parse_definition(variables)
        if ("variables" in definition) and ("file" in definition.get("variables")):
            with open(definition["variables"]["file"], "r") as f:
                var_templatized = Template(f.read())
                external_variables = yaml.safe_load(var_templatized.render(variables))
                variables.update(external_variables)
                definition_with_vars = self.parse_definition(variables )

        else:
            definition_with_vars = definition
        return definition_with_vars




