import logging
import os
import sys
import subprocess
import boto3

from ... import db
from ...db.api import Environment, Pipeline
from ...aws.handlers.sts import SessionHelper
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CDKPipelineStack:
    """
    Create a stack that contains CDK Continuous Integration and Delivery (CI/CD) pipeline.

    The pipeline is based on AWS DDK CICD CodePipeline pipelines

    - Defaults for source/synth - CodeCommit & cdk synth
    - blueprint with DDK application code added in the CodeCommit repository <https://github.com/awslabs/aws-ddk>
    - ability to define development stages: dev, test, prod
    - Ability to connect to private artifactory to pull artifacts from at synth
    - Security best practices - ensures pipeline buckets block non-SSL, and are KMS-encrypted with rotated keys
    - data.all metadata as environment variables accesible at synth

    """
    def get_engine(self):
        envname = os.environ.get("envname", "local")
        engine = db.get_engine(envname=envname)
        return engine

    module_name = __file__

    def __init__(self, target_uri):
        engine = self.get_engine()
        with engine.scoped_session() as session:

            self.pipeline = Pipeline.get_pipeline_by_uri(session, target_uri)
            self.pipeline_environment = Environment.get_environment_by_uri(session, self.pipeline.environmentUri)
            # Development environments
            self.development_environments = Pipeline.query_pipeline_environments(session, target_uri)

        self.env, aws = CDKPipelineStack._set_env_vars(self.pipeline_environment)

        self.code_dir_path = os.path.dirname(os.path.abspath(__file__))

        try:
            codecommit_client = aws.client('codecommit', region_name=self.pipeline_environment.region)
            repository = CDKPipelineStack._check_repository(codecommit_client, self.pipeline.repo)
            if repository:
                self.venv_name = None
                self.code_dir_path = os.path.realpath(
                    os.path.abspath(
                        os.path.join(
                            __file__, "..", "..", "..", "..", "blueprints", "data_pipeline_blueprint"
                        )
                    )
                )
                CDKPipelineStack.write_ddk_json_multienvironment(path=self.code_dir_path, output_file="ddk.json", pipeline_environment=self.pipeline_environment, development_environments=self.development_environments)
                CDKPipelineStack.write_ddk_app_multienvironment(path=self.code_dir_path, output_file="app.py", pipeline=self.pipeline, development_environments=self.development_environments)

                logger.info(f"Pipeline Repo {self.pipeline.repo} Exists...Handling Update")
                update_cmds = [
                    f'REPO_NAME={self.pipeline.repo}',
                    'COMMITID=$(aws codecommit get-branch --repository-name ${REPO_NAME} --branch-name main --query branch.commitId --output text)',
                    'aws codecommit put-file --repository-name ${REPO_NAME} --branch-name main --file-content file://ddk.json --file-path ddk.json --parent-commit-id ${COMMITID} --cli-binary-format raw-in-base64-out',
                    'COMMITID=$(aws codecommit get-branch --repository-name ${REPO_NAME} --branch-name main --query branch.commitId --output text)',
                    'aws codecommit put-file --repository-name ${REPO_NAME} --branch-name main --file-content file://app.py --file-path app.py --parent-commit-id ${COMMITID} --cli-binary-format raw-in-base64-out',
                ]

                process = subprocess.run(
                    "; ".join(update_cmds),
                    text=True,
                    shell=True,  # nosec
                    encoding='utf-8',
                    cwd=self.code_dir_path,
                    env=self.env
                )
            else:
                raise Exception
        except Exception as e:
            self.venv_name = self.initialize_repo()
            CDKPipelineStack.write_ddk_app_multienvironment(path=os.path.join(self.code_dir_path, self.pipeline.repo), output_file="app.py", pipeline=self.pipeline, development_environments=self.development_environments)
            CDKPipelineStack.write_ddk_json_multienvironment(path=os.path.join(self.code_dir_path, self.pipeline.repo), output_file="ddk.json", pipeline_environment=self.pipeline_environment, development_environments=self.development_environments)
            self.git_push_repo()

    def initialize_repo(self):
        venv_name = ".venv"
        cmd_init = [
            f"ddk init {self.pipeline.repo} --generate-only",
            f"cd {self.pipeline.repo}",
            "git init --initial-branch main",
            f"ddk create-repository {self.pipeline.repo} -t application dataall -t team {self.pipeline.SamlGroupName}"
        ]

        logger.info(f"Running Commands: {'; '.join(cmd_init)}")

        process = subprocess.run(
            '; '.join(cmd_init),
            text=True,
            shell=True,  # nosec
            encoding='utf-8',
            cwd=self.code_dir_path,
            env=self.env
        )
        if process.returncode == 0:
            logger.info("Successfully Initialized New CDK/DDK App")

            return venv_name

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
from ddk_app.ddk_app_stack import DdkApplicationStack
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
        DdkApplicationStack(self, "DataPipeline-{pipeline.label}-{pipeline.DataPipelineUri}", environment_id)

id = f"dataall-cdkpipeline-{pipeline.DataPipelineUri}"
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

    def git_push_repo(self):
        git_cmds = [
            'git config user.email "codebuild@example.com"',
            'git config user.name "CodeBuild"',
            'git config --local credential.helper "!aws codecommit credential-helper $@"',
            "git config --local credential.UseHttpPath true",
            "git add .",
            "git commit -a -m 'Initial Commit' ",
            "git push -u origin main"
        ]

        logger.info(f"Running Commands: {'; '.join(git_cmds)}")

        process = subprocess.run(
            '; '.join(git_cmds),
            text=True,
            shell=True,  # nosec
            encoding='utf-8',
            cwd=os.path.join(self.code_dir_path, self.pipeline.repo),
            env=self.env
        )
        if process.returncode == 0:
            logger.info("Successfully Pushed DDK App Code")

    @staticmethod
    def clean_up_repo(path):
        if path:
            precmd = [
                'deactivate;',
                'rm',
                '-rf',
                f"{path}"
            ]

            cwd = os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Running command : \n {' '.join(precmd)}")

            process = subprocess.run(
                ' '.join(precmd),
                text=True,
                shell=True,  # nosec
                encoding='utf-8',
                capture_output=True,
                cwd=cwd
            )

            if process.returncode == 0:
                print(f"Successfully cleaned cloned repo: {path}. {str(process.stdout)}")
            else:
                logger.error(
                    f'Failed clean cloned repo: {path} due to {str(process.stderr)}'
                )
        else:
            logger.info(f"Info:Path {path} not found")
        return

    @staticmethod
    def _check_repository(codecommit_client, repo_name):
        repository = None
        logger.info(f"Checking Repository Exists: {repo_name}")
        try:
            repository = codecommit_client.get_repository(repositoryName=repo_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryDoesNotExistException':
                logger.debug(f'Repository does not exists {repo_name} %s', e)
            else:
                raise e
        return repository if repository else None

    @staticmethod
    def _set_env_vars(pipeline_environment):
        aws = SessionHelper.remote_session(pipeline_environment.AwsAccountId)
        env_creds = aws.get_credentials()

        python_path = '/:'.join(sys.path)[1:] + ':/code' + os.getenv('PATH')

        env = {
            'AWS_REGION': pipeline_environment.region,
            'AWS_DEFAULT_REGION': pipeline_environment.region,
            'CURRENT_AWS_ACCOUNT': pipeline_environment.AwsAccountId,
            'PYTHONPATH': python_path,
            'PATH': python_path,
            'envname': os.environ.get('envname', 'local'),
        }
        if env_creds:
            env.update(
                {
                    'AWS_ACCESS_KEY_ID': env_creds.access_key,
                    'AWS_SECRET_ACCESS_KEY': env_creds.secret_key,
                    'AWS_SESSION_TOKEN': env_creds.token
                }
            )
        return env, aws
