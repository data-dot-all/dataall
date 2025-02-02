import logging
import os
import sys
import subprocess

from botocore.exceptions import ClientError

from dataall.base import db
from dataall.base.aws.sts import SessionHelper
from dataall.base.utils.shell_utils import CommandSanitizer
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.datapipelines.db.datapipelines_repositories import DatapipelinesRepository


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
        envname = os.environ.get('envname', 'local')
        engine = db.get_engine(envname=envname)
        return engine

    module_name = __file__

    def __init__(self, target_uri):
        engine = self.get_engine()
        with engine.scoped_session() as session:
            self.pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, target_uri)
            self.pipeline_environment = EnvironmentService.get_environment_by_uri(session, self.pipeline.environmentUri)
            # Development environments
            self.development_environments = DatapipelinesRepository.query_pipeline_environments(session, target_uri)

        self.env, aws = CDKPipelineStack._set_env_vars(self.pipeline_environment)

        self.code_dir_path = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blueprints'))
        self.is_create = True
        try:
            codecommit_client = aws.client('codecommit', region_name=self.pipeline.region)
            repository = CDKPipelineStack._check_repository(codecommit_client, self.pipeline.repo)
            if repository:
                self.is_create = False
                self.code_dir_path = os.path.realpath(
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blueprints', 'data_pipeline_blueprint')
                )
                CDKPipelineStack.write_ddk_json_multienvironment(
                    path=os.path.join(self.code_dir_path, self.pipeline.repo),
                    output_file='ddk.json',
                    pipeline_environment=self.pipeline_environment,
                    development_environments=self.development_environments,
                    pipeline_name=self.pipeline.name,
                )
                CDKPipelineStack.write_ddk_app_multienvironment(
                    path=os.path.join(self.code_dir_path, self.pipeline.repo),
                    output_file='app.py',
                    pipeline=self.pipeline,
                    development_environments=self.development_environments,
                    pipeline_environment=self.pipeline_environment,
                )

                logger.info(f'Pipeline Repo {self.pipeline.repo} Exists...Handling Update')
                update_cmds = [
                    f'REPO_NAME={self.pipeline.repo}',
                    'COMMITID=$(aws codecommit get-branch --repository-name ${REPO_NAME} --branch-name main --query branch.commitId --output text)',
                    'aws codecommit put-file --repository-name ${REPO_NAME} --branch-name main --file-content file://${REPO_NAME}/ddk.json --file-path ddk.json --parent-commit-id ${COMMITID} --cli-binary-format raw-in-base64-out',
                    'COMMITID=$(aws codecommit get-branch --repository-name ${REPO_NAME} --branch-name main --query branch.commitId --output text)',
                    'aws codecommit put-file --repository-name ${REPO_NAME} --branch-name main --file-content file://${REPO_NAME}/app.py --file-path app.py --parent-commit-id ${COMMITID} --cli-binary-format raw-in-base64-out',
                ]
                CommandSanitizer(args=[self.pipeline.repo])

                # This command is too complex to be executed as a list of commands. We need to run it with shell=True
                # However, the input arguments have be sanitized with the CommandSanitizer

                process = subprocess.run(  # nosemgrep
                    '; '.join(update_cmds),  # nosemgrep
                    text=True,  # nosemgrep
                    shell=True,  # nosec  # nosemgrep
                    encoding='utf-8',  # nosemgrep
                    cwd=self.code_dir_path,  # nosemgrep
                    env=self.env,  # nosemgrep
                )
            else:
                raise Exception
        except Exception:
            self.initialize_repo()
            CDKPipelineStack.write_ddk_app_multienvironment(
                path=os.path.join(self.code_dir_path, self.pipeline.repo),
                output_file='app.py',
                pipeline=self.pipeline,
                development_environments=self.development_environments,
                pipeline_environment=self.pipeline_environment,
            )
            CDKPipelineStack.write_ddk_json_multienvironment(
                path=os.path.join(self.code_dir_path, self.pipeline.repo),
                output_file='ddk.json',
                pipeline_environment=self.pipeline_environment,
                development_environments=self.development_environments,
                pipeline_name=self.pipeline.name,
            )
            self.git_push_repo()

    def initialize_repo(self):
        cmd_init = [
            f'mkdir {self.pipeline.repo}',
            f'cp -R data_pipeline_blueprint/* {self.pipeline.repo}/',
            f'cd {self.pipeline.repo}',
            'git init --initial-branch main',
            f"REPO_URL=$(aws codecommit create-repository --repository-name {self.pipeline.repo} --tags application=dataall,team={self.pipeline.SamlGroupName} --query 'repositoryMetadata.cloneUrlHttp' --output text)",
            'git remote add origin ${REPO_URL}',
        ]

        logger.info(f'Running Commands: {"; ".join(cmd_init)}')

        CommandSanitizer(args=[self.pipeline.repo, self.pipeline.SamlGroupName])

        # This command is too complex to be executed as a list of commands. We need to run it with shell=True
        # However, the input arguments have be sanitized with the CommandSanitizer

        process = subprocess.run(  # nosemgrep
            '; '.join(cmd_init),  # nosemgrep
            text=True,  # nosemgrep
            shell=True,  # nosec  # nosemgrep
            encoding='utf-8',  # nosemgrep
            cwd=self.code_dir_path,  # nosemgrep
            env=self.env,  # nosemgrep
        )
        if process.returncode == 0:
            logger.info('Successfully Initialized New CDK/DDK App')

    @staticmethod
    def write_ddk_json_multienvironment(
        path, output_file, pipeline_environment, development_environments, pipeline_name
    ):
        json_envs = ''
        for env in development_environments:
            json_env = f""",
        "{env.stage}": {{
            "account": "{env.AwsAccountId}",
            "region": "{env.region}",
            "tags": {{
                "Team": "{env.samlGroupName}"
            }}
        }}"""
            json_envs = json_envs + json_env

        json = f"""{{
    "tags": {{
        "dataall": "true",
        "Target": "{pipeline_name}"
    }},
    "environments": {{
        "cicd": {{
            "account": "{pipeline_environment.AwsAccountId}",
            "region": "{pipeline_environment.region}"
        }}{json_envs}
    }}
}}"""
        os.makedirs(path, exist_ok=True)
        with open(f'{path}/{output_file}', 'w') as text_file:
            print(json, file=text_file)

    @staticmethod
    def write_ddk_app_multienvironment(path, output_file, pipeline, development_environments, pipeline_environment):
        header = f"""
# !/usr/bin/env python3

import aws_cdk as cdk
import aws_ddk_core as ddk
from dataall_pipeline_app.dataall_pipeline_app_stack import DataallPipelineStack

app = cdk.App()

class ApplicationStage(cdk.Stage):
    def __init__(
            self,
            scope,
            environment_id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, f"dataall-{{environment_id.title()}}", **kwargs)
        DataallPipelineStack(self, "{pipeline.name}-DataallPipelineStack", environment_id)

id = f"{pipeline_environment.resourcePrefix}-cdkpipeline-{pipeline.DataPipelineUri}"
cicd_pipeline = (
    ddk.CICDPipelineStack(
        app,
        id=id,
        pipeline_name="{pipeline.name}",
        description="Cloud formation stack of PIPELINE: {pipeline.label}; URI: {pipeline.DataPipelineUri}; DESCRIPTION: {pipeline.description}",
        cdk_language="python",
        env=ddk.Configurator.get_environment(
            config_path="./ddk.json", environment_id="cicd"
        ),
    )
        .add_source_action(repository_name="{pipeline.repo}")
        .add_synth_action()
        .build_pipeline()"""

        stages = ''
        for env in sorted(development_environments, key=lambda env: env.order):
            stage = f""".add_stage(stage_id="{env.stage}", stage=ApplicationStage(app, "{env.stage}", env=ddk.Configurator.get_environment(config_path="./ddk.json", environment_id="{env.stage}")))"""
            stages = stages + stage
        footer = """
        .synth()
)

app.synth()
"""
        app = header + stages + footer
        os.makedirs(path, exist_ok=True)
        with open(f'{path}/{output_file}', 'w') as text_file:
            print(app, file=text_file)

    def git_push_repo(self):
        git_cmds = [
            'git config user.email "codebuild@example.com"',
            'git config user.name "CodeBuild"',
            'git config --local credential.helper "!aws codecommit credential-helper $@"',
            'git config --local credential.UseHttpPath true',
            'git add .',
            "git commit -a -m 'Initial Commit' ",
            'git push -u origin main',
        ]

        logger.info(f'Running Commands: {"; ".join(git_cmds)}')

        # This command does not include any customer upstream input
        # no sanitization is needed and shell=true does not impose a risk

        process = subprocess.run(  # nosemgrep
            '; '.join(git_cmds),  # nosemgrep
            text=True,  # nosemgrep
            shell=True,  # nosec  # nosemgrep
            encoding='utf-8',  # nosemgrep
            cwd=os.path.join(self.code_dir_path, self.pipeline.repo),  # nosemgrep
            env=self.env,  # nosemgrep
        )
        if process.returncode == 0:
            logger.info('Successfully Pushed DDK App Code')

    @staticmethod
    def clean_up_repo(pipeline_dir):
        if pipeline_dir:
            code_dir_path = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blueprints'))

            cmd = ['rm', '-rf', f'./{pipeline_dir}']
            logger.info(f'Running command : \n {" ".join(cmd)}')

            process = subprocess.run(
                cmd, text=True, shell=False, encoding='utf-8', capture_output=True, cwd=code_dir_path
            )

            if process.returncode == 0:
                print(f'Successfully cleaned cloned repo: {pipeline_dir}. {str(process.stdout)}')
            else:
                logger.error(f'Failed clean cloned repo: {pipeline_dir} due to {str(process.stderr)}')
        else:
            logger.info(f'Info:Path {pipeline_dir} not found')
        return

    @staticmethod
    def _check_repository(codecommit_client, repo_name):
        repository = None
        logger.info(f'Checking Repository Exists: {repo_name}')
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
        aws = SessionHelper.remote_session(pipeline_environment.AwsAccountId, pipeline_environment.region)
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
                    'AWS_SESSION_TOKEN': env_creds.token,
                }
            )
        return env, aws
