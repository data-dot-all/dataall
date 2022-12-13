import logging
import os
import shutil

from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_codecommit as codecommit

from aws_cdk.aws_s3_assets import Asset

from .manager import stack
from ... import db
from ...db import models
from ...db.api import Environment, Pipeline, Dataset
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack("cdkrepo")
class CDKPipelineStack(Stack):
    """
    Create a stack that contains CDK Continuous Integration and Delivery (CI/CD) pipeline.

    The pipeline is based on CodePipeline pipelines

    - Defaults for source/synth - CodeCommit & cdk synth
    - blueprint with DDK application code added in the CodeCommit repository <https://github.com/awslabs/aws-ddk>
    - ability to define development stages: dev, test, prod
    - ability to select gitflow or trunk-based as development strategy
    - Ability to connect to private artifactory to pull artifacts from at synth
    - Security best practices - ensures pipeline buckets block non-SSL, and are KMS-encrypted with rotated keys
    - data.all metadata as environment variables accesible at synth

    """

    module_name = __file__

    def get_engine(self):
        envname = os.environ.get("envname", "local")
        engine = db.get_engine(envname=envname)
        return engine

    def get_target(self, target_uri) -> models.DataPipeline:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            return Pipeline.get_pipeline_by_uri(session, target_uri)

    def get_pipeline_environments(self, targer_uri) -> models.DataPipelineEnvironment:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            envs = Pipeline.query_pipeline_environments(
                session, targer_uri
            )
        return envs

    def get_pipeline_cicd_environment(
        self, pipeline: models.DataPipeline
    ) -> models.Environment:
        envname = os.environ.get("envname", "local")
        engine = db.get_engine(envname=envname)
        with engine.scoped_session() as session:
            return Environment.get_environment_by_uri(session, pipeline.environmentUri)

    def get_env_team(self, pipeline: models.DataPipeline) -> models.EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(
                session, pipeline.SamlGroupName, pipeline.environmentUri
            )
        return env

    def get_dataset(self, dataset_uri) -> models.Dataset:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            ds = Dataset.get_dataset_by_uri(
                session, dataset_uri
            )
        return ds

    def __init__(self, scope, id, target_uri: str = None, **kwargs):
        kwargs.setdefault("tags", {}).update({"utility": "dataall-data-pipeline"})
        super().__init__(
            scope,
            id,
            env=kwargs.get("env"),
            stack_name=kwargs.get("stack_name"),
            tags=kwargs.get("tags"),
            description="Cloud formation stack of PIPELINE: {}; URI: {}; DESCRIPTION: {}".format(
                self.get_target(target_uri=target_uri).label,
                target_uri,
                self.get_target(target_uri=target_uri).description,
            )[
                :1024
            ],
        )

        # Configuration
        self.target_uri = target_uri

        pipeline = self.get_target(target_uri=target_uri)
        pipeline_environment = self.get_pipeline_cicd_environment(pipeline=pipeline)
        pipeline_env_team = self.get_env_team(pipeline=pipeline)
        # Development environments
        development_environments = self.get_pipeline_environments(targer_uri=target_uri)

        # Create CodeCommit repository and mirror blueprint code
        code_dir_path = os.path.realpath(
            os.path.abspath(
                os.path.join(
                    __file__, "..", "..", "..", "..", "blueprints", "cdk_data_pipeline_blueprint"
                )
            )
        )

        CDKPipelineStack.write_ddk_app_multienvironment(
            path=code_dir_path,
            output_file="app.py",
            pipeline=pipeline,
            development_environments=development_environments
        )

        CDKPipelineStack.write_ddk_json_multienvironment(
            path=code_dir_path,
            output_file="ddk.json",
            pipeline_environment=pipeline_environment,
            development_environments=development_environments
        )
        CDKPipelineStack.cleanup_zip_directory(code_dir_path)

        CDKPipelineStack.zip_directory(code_dir_path)

        code_asset = Asset(
            scope=self, id=f"{pipeline.name}-asset", path=f"{code_dir_path}/code.zip"
        )

        code = codecommit.CfnRepository.CodeProperty(
            s3=codecommit.CfnRepository.S3Property(
                bucket=code_asset.s3_bucket_name,
                key=code_asset.s3_object_key,
            )
        )

        repository = codecommit.CfnRepository(
            scope=self,
            code=code,
            id="CodecommitRepository",
            repository_name=pipeline.repo,
        )

        # CloudFormation output
        CfnOutput(
            self,
            "RepoNameOutput",
            export_name=f"{pipeline.DataPipelineUri}-RepositoryName",
            value=pipeline.repo,
        )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)

        CDKPipelineStack.cleanup_zip_directory(code_dir_path)

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

    @staticmethod
    def write_ddk_app_multienvironment(path, output_file, pipeline, development_environments):
        header = f"""
# !/usr/bin/env python3

import aws_cdk as cdk
from aws_ddk_core.cicd import CICDPipelineStack
from ddk_app.ddk_app_stack import DDKApplicationStack
from aws_ddk_core.config import Config

app = cdk.App()

class ApplicationStage(cdk.Stage):
    def __init__(
            self,
            scope,
            environment_id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, f"dataall-{{environment_id.title()}}", **kwargs)
        DDKApplicationStack(self, "DataPipeline-{pipeline.label}-{pipeline.DataPipelineUri}", environment_id)

id = f"dataall-cdkpipeline-{pipeline.DataPipelineUri}pip"
config = Config()
(
    CICDPipelineStack(
        app,
        id=id,
        environment_id="cicd",
        pipeline_name="{pipeline.label}",
    )
        .add_source_action(repository_name="{pipeline.repo}")
        .add_synth_action()
        .build()"""

        stages = ""
        for env in sorted(development_environments, key=lambda env: env.order):
            stage = f""".add_stage("{env.stage}", ApplicationStage(app, "{env.stage}", env=config.get_env("{env.stage}")))"""
            stages = stages + stage
        footer = """
        .synth()
)

app.synth()
"""
        app = header + stages + footer
        with open(f'{path}/{output_file}', 'w') as text_file:
            print(app, file=text_file)
