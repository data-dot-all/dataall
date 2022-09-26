import logging
import os
import shutil
from typing import List


from aws_cdk import aws_codebuild as codebuild, Stack, RemovalPolicy, CfnOutput
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions

from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms

from aws_cdk.aws_s3_assets import Asset

from .manager import stack
from ... import db
from ...db import models
from ...db.api import Environment, Pipeline, Dataset
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@app("ddk-pipeline")
class PipelineApp:
    """
    Initializes a DDK app with a stack that contains CDK Continuous Integration and Delivery (CI/CD) pipeline.

    The pipeline is based on `CDK self-mutating pipeline
    <https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html>`
    But with some additional features

    - Defaults for source/synth - CodeCommit & cdk synth
    - blueprint with DDK application code added in the CodeCommit repository <https://github.com/awslabs/aws-ddk>
    - ability to define development stages: dev, test, prod
    - ability to select gitflow or trunk-based as development strategy
    - Ability to connect to private artifactory to pull artifacts from at synth
    - Security best practices - ensures pipeline buckets block non-SSL, and are KMS-encrypted with rotated keys
    - data.all metadata as environment variables accesible at synth

    """

    module_name = __file__

    @staticmethod
    def zip_directory(path):
        try:
            shutil.make_archive("code", "zip", path)
            shutil.move("code.zip", f"{path}/code.zip")
        except Exception as e:
            logger.error(f"Failed to zip repository due to: {e}")

    @staticmethod
    def cleanup_zip_directory(path):
        if os.path.isfile(f"{path}/code.zip"):
            os.remove(f"{path}/code.zip")
        else:
            logger.info("Info: %s Zip not found" % f"{path}/code.zip")

    @staticmethod
    def make_environment_variables(
        pipeline,
        pipeline_environment,
        pipeline_env_team,
        stage
    ):

        env_vars_1 = {
            "PIPELINE_URI": codebuild.BuildEnvironmentVariable(value=pipeline.DataPipelineUri),
            "PIPELINE_NAME": codebuild.BuildEnvironmentVariable(value=pipeline.name),
            "STAGE": codebuild.BuildEnvironmentVariable(value=stage),
            "DEV_STRATEGY": codebuild.BuildEnvironmentVariable(value=pipeline.devStrategy),
            "TEMPLATE": codebuild.BuildEnvironmentVariable(value=pipeline.template),
            "ENVIRONMENT_URI": codebuild.BuildEnvironmentVariable(value=pipeline_environment.environmentUri),
            "AWSACCOUNTID": codebuild.BuildEnvironmentVariable(value=pipeline_environment.AwsAccountId),
            "AWSREGION": codebuild.BuildEnvironmentVariable(value=pipeline_environment.region),
            "ENVTEAM_ROLENAME": codebuild.BuildEnvironmentVariable(value=pipeline_env_team),
        }
        env_vars = dict(env_vars_1)
        return env_vars

    @staticmethod
    def write_init_deploy_buildspec(path, output_file):
        yaml = """
            version: '0.2'
            env:
                git-credential-helper: yes
            phases:
              pre_build:
                commands:
                - n 16.15.1
                - npm install -g aws-cdk
                - pip install aws-ddk
                - git config --global user.email "codebuild@example.com"
                - git config --global user.name "CodeBuild"
                - echo ${CODEBUILD_BUILD_NUMBER}
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" ]] ; then echo "${TEMPLATE}"; else echo "not first build"; fi
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" && "${TEMPLATE}" == "" ]] ; then git clone "https://git-codecommit.${AWS_REGION}.amazonaws.com/v1/repos/${PIPELINE_NAME}"; cd $PIPELINE_NAME; git checkout main; ddk init --generate-only ddk-app; cp -R ddk-app/* ./; rm -r ddk-app; cp dataall_ddk.json ./ddk.json; cp multiapp.py ./app.py; rm multiapp.py dataall_ddk.json; git add .; git commit -m "First Commit from CodeBuild - DDK application"; git push --set-upstream origin main; else echo "not first build"; fi
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" && "${TEMPLATE}" != "" ]] ; then git clone "https://git-codecommit.${AWS_REGION}.amazonaws.com/v1/repos/${PIPELINE_NAME}"; cd $PIPELINE_NAME; git checkout main; ddk init --generate-only --template $TEMPLATE ddk-app; cp -R ddk-app/* ./; rm -r ddk-app; cp dataall_ddk.json ./ddk.json; cp multiapp.py ./app.py; rm multiapp.py dataall_ddk.json; git add .; git commit -m "First Commit from CodeBuild - DDK application"; git push --set-upstream origin main; else echo "not first build"; fi
                - pip install -r requirements.txt
              build:
                commands:
                    - aws sts get-caller-identity
                    - ddk deploy
        """
        with open(f'{path}/{output_file}', 'w') as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def write_init_branches_deploy_buildspec(path, output_file):
        yaml = """
            version: '0.2'
            env:
                git-credential-helper: yes
            phases:
              install:
                commands:
                - 'n 16.15.1'
              pre_build:
                commands:
                - n 16.15.1
                - npm install -g aws-cdk
                - pip install aws-ddk
                - git config --global user.email "codebuild@example.com"
                - git config --global user.name "CodeBuild"
                - echo ${CODEBUILD_BUILD_NUMBER}
                - echo ${TEMPLATE}
                - echo ${DEV_STAGES}
                - echo ${STAGE}
                - stages=$(echo $DEV_STAGES | tr ",","\n")
                - for stage in $stages; do echo $stage; done
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" ]] ; then echo "${TEMPLATE}"; else echo "not first build"; fi
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" && "${TEMPLATE}" == "" ]] ; then git clone "https://git-codecommit.${AWS_REGION}.amazonaws.com/v1/repos/${PIPELINE_NAME}"; cd $PIPELINE_NAME; git checkout main; ddk init --generate-only ddk-app; cp -R ddk-app/* ./; rm -r ddk-app; cp dataall_ddk.json ./ddk.json; cp multiapp.py ./app.py; rm multiapp.py dataall_ddk.json; git add .; git commit -m "First Commit from CodeBuild - DDK application"; git push --set-upstream origin main; else echo "not first build"; fi
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" && "${TEMPLATE}" != "" ]] ; then git clone "https://git-codecommit.${AWS_REGION}.amazonaws.com/v1/repos/${PIPELINE_NAME}"; cd $PIPELINE_NAME; git checkout main; ddk init --generate-only --template $TEMPLATE ddk-app; cp -R ddk-app/* ./; rm -r ddk-app; cp dataall_ddk.json ./ddk.json; cp multiapp.py ./app.py; rm multiapp.py dataall_ddk.json; git add .; git commit -m "First Commit from CodeBuild - DDK application"; git push --set-upstream origin main; else echo "not first build"; fi
                - if [[ "${CODEBUILD_BUILD_NUMBER}" == "1" ]] ; then git clone "https://git-codecommit.${AWS_REGION}.amazonaws.com/v1/repos/${PIPELINE_NAME}"; cd $PIPELINE_NAME; for stage in $stages; do if [[$stage != "prod" ]]; then git checkout $stage; git push --set-upstream origin $stage; fi; done; else echo "not first build"; fi
                - pip install -r requirements.txt
              build:
                commands:
                    - aws sts get-caller-identity
                    - ddk deploy
        """
        with open(f'{path}/{output_file}', 'w') as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def write_deploy_buildspec(path, output_file):
        yaml = """
            version: '0.2'
            env:
                git-credential-helper: yes
            phases:
              pre_build:
                commands:
                - n 16.15.1
                - npm install -g aws-cdk
                - pip install aws-ddk
                - pip install -r requirements.txt
              build:
                commands:
                - aws sts get-caller-identity
                - ddk deploy
        """
        with open(f'{path}/{output_file}', 'w') as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def make_codebuild_policy_statements(
            pipeline_environment,
            pipeline_env_team,
            pipeline
    ) -> List[iam.PolicyStatement]:
        return[
            iam.PolicyStatement(
                actions=[
                    "ec2:DescribeAvailabilityZones",
                    "kms:Decrypt",
                    "kms:Encrypt",
                    "kms:GenerateDataKey",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "ssm:GetParametersByPath",
                    "ssm:GetParameters",
                    "ssm:GetParameter",
                    "codebuild:CreateReportGroup",
                    "codebuild:CreateReport",
                    "codebuild:UpdateReport",
                    "codebuild:BatchPutTestCases",
                    "codebuild:BatchPutCodeCoverages",
                    "codecommit:ListRepositories",
                    "sts:AssumeRole",
                    "cloudformation:DescribeStacks"
                ],
                resources=["*"],
            ),
            iam.PolicyStatement(
                actions=[
                    "codecommit:*"
                ],
                resources=[f"arn:aws:codecommit:{pipeline_environment.region}:{pipeline_environment.AwsAccountId}:{pipeline.repo}"],
            )


        ]

    @staticmethod
    def write_ddk_json_multienvironment(path, output_file, pipeline_environment, development_environments):
        json_envs = ""
        for env in development_environments:
            json_env = f""",
        "{env.stage}": {{
            "account": "{env.AwsAccountId}",
            "region": "{env.region}",
            "resources": {{
                "ddk-bucket": {{"versioned": false, "removal_policy": "destroy"}}
            }}
        }}"""
            json_envs = json_envs + json_env

        json = f"""{{
    "environments": {{
        "cicd": {{
            "account": "{pipeline_environment.AwsAccountId}",
            "region": "{pipeline_environment.region}"
        }}{json_envs}
    }}
}}"""

        with open(f'{path}/{output_file}', 'w') as text_file:
            print(json, file=text_file)
