import logging
import os
import shutil

from aws_cdk import aws_codebuild as codebuild, Stack, RemovalPolicy, CfnOutput
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as codepipeline_actions
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm
from aws_cdk.aws_s3_assets import Asset

from .manager import stack
from ... import db
from ...db import models
from ...db.api import Environment, Pipeline
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack("pipeline")
class PipelineStack(Stack):

    module_name = __file__

    def get_engine(self):
        envname = os.environ.get("envname", "local")
        engine = db.get_engine(envname=envname)
        return engine

    def get_target(self, target_uri) -> models.SqlPipeline:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            return Pipeline.get_pipeline_by_uri(session, target_uri)

    def get_pipeline_environment(self, pipeline: models.SqlPipeline) -> models.Environment:
        envname = os.environ.get("envname", "local")
        engine = db.get_engine(envname=envname)
        with engine.scoped_session() as session:
            return Environment.get_environment_by_uri(session, pipeline.environmentUri)

    def get_env_group(self, pipeline: models.SqlPipeline) -> models.EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(session, pipeline.SamlGroupName, pipeline.environmentUri)
        return env

    def define_stage(
        self,
        pipeline: models.SqlPipeline,
        account_id,
        stage,
        region,
        environment_uri,
        bucket_name,
        ecr_repository,
        build_project_role,
        pipeline_environment,
        build_spec,
        run_build_spec,
        environment_iam_role: iam.Role,
    ):

        build_project = self.make_pipeline_project(
            pipeline=pipeline,
            account_id=account_id,
            id_element=f"build{stage}",
            region=region,
            environment_uri=environment_uri,
            environment_iam_role=environment_iam_role,
            bucket_name=bucket_name,
            repository_uri=ecr_repository,
            build_project_role=build_project_role,
            build_spec=build_spec,
            stage=stage,
        )

        build_project_run_tests = self.make_pipeline_project(
            id_element=f"build-run-tests{stage}",
            pipeline=pipeline,
            account_id=account_id,
            region=region,
            environment_uri=environment_uri,
            environment_iam_role=environment_iam_role,
            bucket_name=bucket_name,
            repository_uri=ecr_repository,
            build_project_role=build_project_role,
            build_spec=run_build_spec,
            stage=stage,
        )

        self.codepipeline_pipeline.add_stage(
            stage_name=f"Deploy{stage}Stage",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name=f"deploy{stage}",
                    input=self.source_artifact,
                    project=build_project,
                    outputs=[codepipeline.Artifact()],
                )
            ],
        )

        if stage != "prod":
            self.codepipeline_pipeline.add_stage(
                stage_name=f"RunTests{stage}",
                actions=[
                    codepipeline_actions.CodeBuildAction(
                        action_name="runtest",
                        input=self.source_artifact,
                        project=build_project_run_tests,
                        outputs=[codepipeline.Artifact()],
                    )
                ],
            )

            self.codepipeline_pipeline.add_stage(
                stage_name=f"ManualApproval{stage}",
                actions=[codepipeline_actions.ManualApprovalAction(action_name=f"ManualApproval{stage}")],
            )

    def __init__(self, scope, id, target_uri: str = None, **kwargs):
        kwargs.setdefault("tags", {}).update({"utility": "dataall-data-pipeline"})
        super().__init__(
            scope,
            id,
            env=kwargs.get("env"),
            stack_name=kwargs.get("stack_name"),
            tags=kwargs.get("tags"),
            description="'{}' ({}) dataall code-pipeline for Datapipeline".format(
                self.get_target(target_uri=target_uri).repo, target_uri
            ),
        )

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        pipeline = self.get_target(target_uri=target_uri)
        pipeline_environment = self.get_pipeline_environment(pipeline=pipeline)
        env_group = self.get_env_group(pipeline=pipeline)
        stages = ["test", "prod"]

        environment_role = iam.Role.from_role_arn(self, "EnvRole", env_group.environmentIAMRoleArn)

        pipeline_bucket = s3.Bucket(
            self,
            id=f"{pipeline.repo}-{pipeline_environment.region}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True,
            auto_delete_objects=True,
        )

        code_dir_path = os.path.realpath(
            os.path.abspath(os.path.join(__file__, "..", "..", "..", "..", "blueprints", "ml_data_pipeline"))
        )

        PipelineStack.write_buildspec_files(path=code_dir_path, stages=stages)

        PipelineStack.cleanup_zip_directory(code_dir_path)

        PipelineStack.zip_directory(code_dir_path)

        code_asset = Asset(scope=self, id=f"{pipeline.name}-asset", path=f"{code_dir_path}/code.zip")

        code = codecommit.CfnRepository.CodeProperty(
            s3=codecommit.CfnRepository.S3Property(
                bucket=code_asset.s3_bucket_name,
                key=code_asset.s3_object_key,
            )
        )

        codecommit.CfnRepository(
            scope=self,
            code=code,
            id="gluecoderepo",
            repository_name=pipeline.repo,
        )

        self.codebuild_key = kms.Key(
            self,
            f"{pipeline.name}-codebuild-key",
            removal_policy=RemovalPolicy.DESTROY,
            alias=f"{pipeline.name}-codebuild-key",
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        resources=["*"],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.AccountPrincipal(account_id=self.account),
                        ],
                        actions=["kms:*"],
                    ),
                    iam.PolicyStatement(
                        resources=["*"],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.ServicePrincipal(service="codebuild.amazonaws.com"),
                        ],
                        actions=["kms:GenerateDataKey*", "kms:Decrypt"],
                    ),
                ],
            ),
        )

        role_inline_policy = iam.Policy(
            self,
            f"{pipeline.name}-policy",
            policy_name=f"{pipeline.name}-policy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "ec2:DescribeAvailabilityZones",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetAuthorizationToken",
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
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:Get*",
                        "s3:Put*",
                        "s3:List*",
                    ],
                    resources=[
                        pipeline_bucket.bucket_arn,
                        f"{pipeline_bucket.bucket_arn}/*",
                    ],
                ),
            ],
        )

        build_project_role = iam.Role(
            self,
            "PipelineRole",
            role_name=pipeline.name,
            inline_policies={f"Inline{pipeline.name}": role_inline_policy.document},
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
        )

        ecr_repository = ecr.Repository(
            self,
            f"ecr-{pipeline.name}",
            repository_name=pipeline.name,
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        ecr_repository.grant_pull_push(grantee=build_project_role)
        ecr_repository.grant_pull_push(grantee=environment_role)

        for stage in stages:
            self.set_parameters_on_param_store(
                pipeline,
                pipeline_environment,
                stage,
                pipeline_bucket,
                ecr_repository,
                build_project_role,
                env_group,
            )

        codepipeline_pipeline = codepipeline.Pipeline(
            scope=self,
            id=pipeline.name,
            pipeline_name=pipeline.name,
            restart_execution_on_update=True,
        )
        self.codepipeline_pipeline = codepipeline_pipeline
        self.source_artifact = codepipeline.Artifact()

        codepipeline_pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="CodeCommit",
                    branch="main",
                    output=self.source_artifact,
                    trigger=codepipeline_actions.CodeCommitTrigger.POLL,
                    repository=codecommit.Repository.from_repository_name(
                        self, "source_blueprint_repo", repository_name=pipeline.repo
                    ),
                )
            ],
        )
        build_sagemaker_jobs = self.make_pipeline_project(
            pipeline=pipeline,
            account_id=pipeline_environment.AwsAccountId,
            id_element="build-sagemaker-jobs",
            region=pipeline_environment.region,
            environment_uri=pipeline_environment.environmentUri,
            environment_iam_role=environment_role,
            bucket_name=pipeline_bucket.bucket_name,
            repository_uri=ecr_repository,
            build_project_role=build_project_role,
            build_spec="build_sagemaker_jobs_buildspec.yaml",
            stage="test",
        )
        codepipeline_pipeline.add_stage(
            stage_name="BuildSageMakerJobs",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="BuildSageMakerJobs",
                    input=self.source_artifact,
                    project=build_sagemaker_jobs,
                    outputs=[codepipeline.Artifact()],
                )
            ],
        )

        training_images_project = self.make_pipeline_project(
            pipeline=pipeline,
            account_id=pipeline_environment.AwsAccountId,
            id_element="build-sm-training-images",
            region=pipeline_environment.region,
            environment_uri=pipeline_environment.environmentUri,
            environment_iam_role=environment_role,
            bucket_name=pipeline_bucket.bucket_name,
            repository_uri=ecr_repository,
            build_project_role=build_project_role,
            build_spec="training_image_buildspec.yaml",
            stage="test",
        )
        processing_image_project = self.make_pipeline_project(
            pipeline=pipeline,
            account_id=pipeline_environment.AwsAccountId,
            id_element="build-sm-processing-image",
            region=pipeline_environment.region,
            environment_uri=pipeline_environment.environmentUri,
            environment_iam_role=environment_role,
            bucket_name=pipeline_bucket.bucket_name,
            repository_uri=ecr_repository,
            build_project_role=build_project_role,
            build_spec="processing_image_buildspec.yaml",
            stage="test",
        )

        codepipeline_pipeline.add_stage(
            stage_name="DeployDockerImages",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="DeployProcessingImages",
                    input=self.source_artifact,
                    project=processing_image_project,
                    outputs=[codepipeline.Artifact()],
                ),
                codepipeline_actions.CodeBuildAction(
                    action_name="DeployTrainingImages",
                    input=self.source_artifact,
                    project=training_images_project,
                    outputs=[codepipeline.Artifact()],
                ),
            ],
        )
        for stage in stages:
            self.define_stage(
                pipeline=pipeline,
                account_id=pipeline_environment.AwsAccountId,
                stage=stage,
                region=pipeline_environment.region,
                environment_uri=pipeline_environment.environmentUri,
                environment_iam_role=environment_role,
                bucket_name=pipeline_bucket.bucket_name,
                ecr_repository=ecr_repository,
                build_project_role=build_project_role,
                pipeline_environment=pipeline_environment,
                build_spec=PipelineStack.buildspec_of_stage(stage),
                run_build_spec=PipelineStack.run_test_buildspec_of_stage(stage),
            )

        CfnOutput(
            self,
            "RepoNameOutput",
            export_name=f"{pipeline.sqlPipelineUri}-RepositoryName",
            value=pipeline.repo,
        )
        CfnOutput(
            self,
            "PipelineNameOutput",
            export_name=f"{pipeline.sqlPipelineUri}-PipelineName",
            value=codepipeline_pipeline.pipeline_name,
        )

        for stage in stages:
            CfnOutput(
                self,
                f"Pipeline{stage}Instance",
                export_name=f"{pipeline.sqlPipelineUri}-Pipeline{stage}Instance",
                value=pipeline.name,
            )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)

        PipelineStack.cleanup_zip_directory(code_dir_path)

    def set_parameters_on_param_store(
        self,
        pipeline,
        environment,
        stage,
        bucket,
        ecr_repository,
        code_build_role,
        env_group,
    ):
        codebuild_role = iam.ArnPrincipal(code_build_role.role_arn)
        role = iam.ArnPrincipal(env_group.environmentIAMRoleArn)
        param = aws_ssm.StringParameter(
            self,
            f"bucketname{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/bucket_name",
            string_value=bucket.bucket_name,
        )

        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"accountid{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/accountid",
            string_value=environment.AwsAccountId,
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"pipelinename{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/pipeline_name",
            string_value=f"{pipeline.name}{stage}",
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"pipelineiamrolearn{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/pipeline_iam_role_arn",
            string_value=env_group.environmentIAMRoleArn,
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"fulldevrole{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/fulldev_iam_role",
            string_value=env_group.environmentIAMRoleArn,
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"adminrole{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/admin_iam_role",
            string_value=env_group.environmentIAMRoleArn,
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"pipelineregion{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/pipeline_region",
            string_value=environment.region,
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

        param = aws_ssm.StringParameter(
            self,
            f"pipelineecrrepository{stage}",
            parameter_name=f"/{pipeline.name}/{stage}/ecr_repository_uri",
            string_value=ecr_repository.repository_uri,
        )
        param.grant_read(role)
        param.grant_read(codebuild_role)

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
    def write_run_test_buildspec(path, output_file):
        yaml = """
            version: '0.2'
            phases:
              pre_build:
                commands:
                - npm install -g aws-cdk && pip install -r requirements.txt && pip install -r
                  dev-requirements.txt
                - pip install pytest
                - pip install pytest-cov
                - pip install pytest-spark
              build:
                commands:
                    - python -m pytest --cov=engine --cov=utils --cov-branch --cov-report
                        term-missing --cov-report xml:tests/unittests/test-reports/coverage.xml  --junitxml=tests/unittests/test-reports/junit.xml  tests/unittests
                    - python -m pytest --cov=customcode --cov-branch  --cov-report term-missing
                        --cov-report xml:tests/unittests-custom/test-reports-custom/coverage.xml  --junitxml=tests/unittests-custom/test-reports-custom/junit.xml  tests/unittests-custom
            reports:
              pytest_reports:
                files:
                - junit.xml
                base-directory: tests/unittests/test-reports
                file-format: JUNITXML
              coverage_reports:
                files:
                - coverage.xml
                base-directory: tests/unittests/test-reports
                file-format: COBERTURAXML
              custom_unit_test_reports:
                files:
                - junit.xml
                base-directory: tests/unittests-custom/test-reports-custom
                file-format: JUNITXML
              custom_coverage_reports:
                files:
                - coverage.xml
                base-directory: tests/unittests-custom/test-reports-custom
                file-format: COBERTURAXML
            artifacts:
              files: "**/*"
        """
        with open(f"{path}/{output_file}", "w") as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def write_deploy_stage_buildspec(path, output_file, stage):
        yaml = f"""
            version: '0.2'
            phases:
              pre_build:
                commands:
                - npm install -g aws-cdk && pip install -r requirements.txt
                - mkdir -p libs/
                - mkdir -p dist/
                - mkdir -p jars/
              build:
                commands:
                    - aws sts get-caller-identity
                    - cdk synth
                    - cdk deploy --require-approval never --all
                    - pip install -r glue-requirements.txt -t ./libs
                    - mkdir -p ./libs/pydeequ
                    - mkdir -p ./libs/engine
                    - cp -r engine/glue/pydeequ ./libs/
                    - cp -r customcode/glue/sql_queries ./libs
                    - cp -r customcode/glue/udfs ./libs
                    - cp -r engine/glue ./libs/engine/glue
                    - cd libs
                    - zip -r ../dist/deps.zip ./*
                    - rm -rf ./libs/
                    - aws s3 cp ../config.yaml s3://$BUCKET_NAME/{stage}/config.yaml
                    - aws s3 cp ../engine/glue/glue_main.py  s3://$BUCKET_NAME/{stage}/engine/glue/glue_main.py
                    - aws s3 cp --recursive ../examples/data s3://$BUCKET_NAME/{stage}/data
                    - aws s3 cp --recursive ../customcode/glue/glue_jobs/ s3://$BUCKET_NAME/{stage}/customcode/glue/glue_jobs/
                    - aws s3 cp --recursive ../customcode/glue/sql_queries/ s3://$BUCKET_NAME/{stage}/customcode/glue/sql_queries/
                    - aws s3 cp --recursive ../engine/glue/jars/ s3://$BUCKET_NAME/{stage}/engine/glue/jars
                    - aws s3 cp --recursive ../customcode/glue/variables_files/ s3://$BUCKET_NAME/{stage}/customcode/glue/variables_files/
                    - aws s3 cp ../dist/deps.zip s3://$BUCKET_NAME/{stage}/engine/glue/deps.zip
            artifacts:
              base-directory: cdk.out
              files: "**/*"
        """
        with open(f"{path}/{output_file}", "w") as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def write_build_sagemaker_jobs(path, output_file):
        yaml = """
        version: "0.2"

        phases:
          build:
            commands:
              - if [ -d \"smjobs\" ]; then cd smjobs; fi
              - if [ -d \"smjobs\" ]; then make venv; fi
              - if [ -d \"smjobs\" ]; then make install; fi
          pre_build:
            commands:
              - aws --version
        """
        with open(f"{path}/{output_file}", "w") as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def write_deploy_processing_image_buildspec(path, output_file):
        yaml = """
        version: '0.2'
        phases:
          pre_build:
            commands:
            - aws --version
          build:
            commands:
            - if [ -d "smjobs" ]; then ls smjobs; fi
            - aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 137112412989.dkr.ecr.us-east-1.amazonaws.com
            - if [ -d "smjobs" ]; then docker build -f smjobs/Dockerfile -t $ECR_REPOSITORY .; fi
            - $(aws ecr get-login --region $AWS_DEFAULT_REGION --no-include-email)
            - if [ -d "smjobs" ]; then docker push $ECR_REPOSITORY; fi
        """
        with open(f"{path}/{output_file}", "w") as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def write_deploy_training_image_buildspec(path, output_file):
        yaml = """
        version: "0.2"

        phases:
          build:
            commands:
              - if [ -d \"smjobs\" ]; then ls engine; fi
              - if [ -d \"smjobs\" ]; then python -m engine.sagemaker.image_builder; fi
          pre_build:
            commands:
              - if [ -d \"smjobs\" ]; then pip install -r requirements.txt; fi
              - if [ -d \"smjobs\" ]; then pip install -r dev-requirements.txt; fi
        """
        with open(f"{path}/{output_file}", "w") as text_file:
            print(yaml, file=text_file)

    @staticmethod
    def buildspec_of_stage(stage):
        return f"deploy_{stage}_stage_buildspec.yaml"

    @staticmethod
    def run_test_buildspec_of_stage(stage):
        return f"run_test_buildspec_{stage}.yaml"

    @staticmethod
    def write_buildspec_files(path, stages):
        PipelineStack.write_deploy_training_image_buildspec(path, "build_sagemaker_jobs_buildspec.yaml")
        PipelineStack.write_deploy_processing_image_buildspec(path, "processing_image_buildspec.yaml")
        PipelineStack.write_deploy_training_image_buildspec(path, "training_image_buildspec.yaml")
        for stage in stages:
            PipelineStack.write_deploy_stage_buildspec(path, PipelineStack.buildspec_of_stage(stage), stage)

            PipelineStack.write_run_test_buildspec(path, PipelineStack.run_test_buildspec_of_stage(stage))

    @staticmethod
    def make_environment_variables(
        pipeline,
        id,
        account_id,
        region,
        environment_uri,
        bucket_name,
        environment_role: iam.Role,
        repository_uri,
        stage,
    ):

        pipeline_name = pipeline.name if stage.lower() == "prod" else (pipeline.name + "-" + stage)
        env_vars = {
            "AWSACCOUNTID": codebuild.BuildEnvironmentVariable(value=account_id),
            "AWSREGION": codebuild.BuildEnvironmentVariable(value=region),
            "ORIGIN_PIPELINE_NAME": codebuild.BuildEnvironmentVariable(value=pipeline.name),
            "PIPELINE_NAME": codebuild.BuildEnvironmentVariable(value=pipeline_name),
            "BUCKET_NAME": codebuild.BuildEnvironmentVariable(value=bucket_name),
            "ENVROLEARN": codebuild.BuildEnvironmentVariable(value=environment_role.role_arn),
            "BATCH_INSTANCE_ROLE": codebuild.BuildEnvironmentVariable(value=f"ecsInstanceRole-{environment_uri}"),
            "EC2_SPOT_FLEET_ROLE": codebuild.BuildEnvironmentVariable(
                value=f"AmazonEC2SpotFleetRole-{environment_uri}"
            ),
            "ECR_REPOSITORY": codebuild.BuildEnvironmentVariable(value=repository_uri),
            "ENVIRONMENT_URI": codebuild.BuildEnvironmentVariable(value=environment_uri),
            "PIPELINE_URI": codebuild.BuildEnvironmentVariable(value=pipeline.sqlPipelineUri),
            "SAML_GROUP": codebuild.BuildEnvironmentVariable(value=pipeline.SamlGroupName or ""),
            "STAGE": codebuild.BuildEnvironmentVariable(value=stage),
        }

        return env_vars

    def make_pipeline_project(
        self,
        pipeline: models.SqlPipeline,
        id_element: str,
        account_id: str,
        region: str,
        environment_uri: str,
        environment_iam_role: iam.Role,
        build_project_role: iam.Role,
        bucket_name: str,
        repository_uri: str,
        stage: str,
        build_spec: str,
    ):
        return codebuild.PipelineProject(
            scope=self,
            id=f"{pipeline.name}-{id_element}",
            environment=codebuild.BuildEnvironment(
                privileged=True,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                environment_variables=PipelineStack.make_environment_variables(
                    pipeline=pipeline,
                    id=id_element,
                    account_id=account_id,
                    region=region,
                    environment_uri=environment_uri,
                    environment_role=environment_iam_role,
                    bucket_name=bucket_name,
                    repository_uri=repository_uri,
                    stage=stage,
                ),
            ),
            role=build_project_role,
            build_spec=codebuild.BuildSpec.from_source_filename(build_spec),
            encryption_key=self.codebuild_key,
        )
