import re
import uuid
from typing import List

from aws_cdk import SecretValue, Stack, Tags, RemovalPolicy
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import pipelines
from aws_cdk.pipelines import CodePipelineSource

from .albfront_stage import AlbFrontStage
from .aurora import AuroraServerlessStack
from .backend_stage import BackendStage
from .cloudfront_stage import CloudfrontStage
from .codeartifact import CodeArtifactStack
from .ecr_stage import ECRStage
from .vpc import VpcStack


class PipelineStack(Stack):
    def __init__(
        self,
        id,
        scope,
        target_envs: List = None,
        git_branch='main',
        resource_prefix='dataall',
        source='codecommit',
        **kwargs,
    ):
        super().__init__(id, scope, **kwargs)

        self.validate_deployment_params(git_branch, resource_prefix, target_envs)
        self.git_branch = git_branch
        self.source = source
        self.resource_prefix = resource_prefix
        self.target_envs = target_envs

        self.vpc_stack = VpcStack(
            self,
            id=f'Vpc',
            envname=git_branch,
            cidr='10.0.0.0/16',
            resource_prefix=resource_prefix,
            vpc_id=self.node.try_get_context('tooling_vpc_id'),
            **kwargs,
        )
        self.vpc = self.vpc_stack.vpc

        self.aurora_devdb = AuroraServerlessStack(
            self,
            f'Aurora',
            envname=self.git_branch,
            resource_prefix=self.resource_prefix,
            vpc=self.vpc,
            prod_sizing=False,
            **kwargs,
        )

        self.codebuild_sg = ec2.SecurityGroup(
            self,
            f'{self.resource_prefix}-codebuild-sg',
            security_group_name=f'{self.resource_prefix}-{self.git_branch}-cbprojects-sg',
            vpc=self.vpc,
            allow_all_outbound=True,
        )
        self.aurora_devdb.aurora_sg.add_ingress_rule(
            peer=self.codebuild_sg,
            connection=ec2.Port.tcp(5432),
            description=f'Allow Codebuild to run integration tests',
        )

        self.codeartifact = CodeArtifactStack(
            self,
            f'CodeArtifact',
            target_envs=self.target_envs,
            git_branch=self.git_branch,
            resource_prefix=self.resource_prefix,
        )

        self.codebuild_policy = [
            iam.PolicyStatement(
                actions=[
                    'sts:GetServiceBearerToken',
                ],
                resources=['*'],
                conditions={
                    'StringEquals': {'sts:AWSServiceName': 'codeartifact.amazonaws.com'}
                },
            ),
            iam.PolicyStatement(
                actions=[
                    'ecr:GetAuthorizationToken',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                actions=[
                    'codeartifact:GetAuthorizationToken',
                    'codeartifact:GetRepositoryEndpoint',
                    'codeartifact:ReadFromRepository',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchGetImage',
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:PutImage',
                    'ecr:InitiateLayerUpload',
                    'ecr:UploadLayerPart',
                    'ecr:CompleteLayerUpload',
                    'ecr:GetDownloadUrlForLayer',
                    'kms:Decrypt',
                    'kms:Encrypt',
                    'kms:GenerateDataKey',
                    'secretsmanager:GetSecretValue',
                    'secretsmanager:DescribeSecret',
                    'ssm:GetParametersByPath',
                    'ssm:GetParameters',
                    'ssm:GetParameter',
                    's3:Get*',
                    's3:Put*',
                    's3:List*',
                    'codebuild:CreateReportGroup',
                    'codebuild:CreateReport',
                    'codebuild:UpdateReport',
                    'codebuild:BatchPutTestCases',
                    'codebuild:BatchPutCodeCoverages',
                ],
                resources=[
                    f'arn:aws:s3:::{self.resource_prefix}*',
                    f'arn:aws:s3:::{self.resource_prefix}*/*',
                    f'arn:aws:codebuild:{self.region}:{self.account}:project/*{self.resource_prefix}*',
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                    f'arn:aws:kms:{self.region}:{self.account}:key/*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                    f'arn:aws:ecr:{self.region}:{self.account}:repository/{resource_prefix}*',
                    f'arn:aws:codeartifact:{self.region}:{self.account}:repository/{resource_prefix}*',
                    f'arn:aws:codeartifact:{self.region}:{self.account}:domain/{resource_prefix}*',
                ],
            ),
        ]
        self.pipeline_bucket_name = f'{self.resource_prefix}-{self.git_branch}-code-{self.account}-{self.region}'
        self.pipeline_bucket = s3.Bucket(
            self,
            id='source-code-bucket',
            bucket_name=self.pipeline_bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            encryption=s3.BucketEncryption.S3_MANAGED,
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.HEAD,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.GET,
                    ],
                    allowed_origins=['*'],
                    allowed_headers=['*'],
                    exposed_headers=[],
                )
            ],
            versioned=True,
            enforce_ssl=True,
            auto_delete_objects=True,
        )
        self.pipeline_bucket.grant_read_write(iam.AccountPrincipal(self.account))

        self.pipeline_iam_role = iam.Role(
            self,
            id=f'CDKPipelinesRole{self.git_branch}',
            role_name=f'{self.resource_prefix}-{self.git_branch}-cdkpipelines-role',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('codebuild.amazonaws.com'),
                iam.ServicePrincipal('codepipeline.amazonaws.com'),
                iam.AccountPrincipal(self.account),
            ),
        )
        for policy in self.codebuild_policy:
            self.pipeline_iam_role.add_to_policy(policy)
            
        if self.source == "github":
            source = CodePipelineSource.git_hub(
                repo_string="awslabs/aws-dataall",
                branch=self.git_branch,
                authentication=SecretValue.secrets_manager(secret_id="github-access-token-secret")
            )
            
        else:
            source = CodePipelineSource.code_commit(
                        repository=codecommit.Repository.from_repository_name(
                            self, 'sourcerepo', repository_name='dataall'
                        ),
                        branch=self.git_branch,
                    )

        self.pipeline = pipelines.CodePipeline(
            self,
            f'{self.resource_prefix}-{self.git_branch}-cdkpipeline',
            pipeline_name=f'{self.resource_prefix}-pipeline-{self.git_branch}',
            publish_assets_in_parallel=False,
            synth=pipelines.CodeBuildStep(
                'Synth',
                input=source,
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                ),
                commands=[
                    'n 16.15.1',
                    'yum -y install shadow-utils wget && yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel',
                    f'aws codeartifact login --tool npm --repository {self.codeartifact.npm_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                    'npm install -g aws-cdk',
                    f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                    'pip install -r deploy/requirements.txt',
                    'cdk synth',
                    'echo ${CODEBUILD_SOURCE_VERSION}'
                ],
                role_policy_statements=self.codebuild_policy,
                vpc=self.vpc,
            ),
            cross_account_keys=True,
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    environment_variables={
                        "DATAALL_REPO_BRANCH": codebuild.BuildEnvironmentVariable(
                            value=git_branch
                        ),
                    }
                )
            )
        )

        self.pipeline.node.add_dependency(self.aurora_devdb)

        self.set_quality_gate_stage()

        self.image_tag = f'{git_branch}-{str(uuid.uuid4())[:8]}'

        repository_name = self.set_ecr_stage(
            {'envname': git_branch, 'account': self.account, 'region': self.region}
        )

        target_envs = target_envs or [
            {'envname': 'dev', 'account': self.account, 'region': self.region}
        ]

        for target_env in target_envs:
            self.pipeline_bucket.grant_read(iam.AccountPrincipal(target_env['account']))

            backend_stage = self.set_backend_stage(target_env, repository_name)

            if target_env.get('with_approval'):
                backend_stage.add_pre(
                    pipelines.ManualApprovalStep(
                        id=f"Approve{target_env['envname']}Deployment",
                        comment=f'Approve deployment for environment {target_env["envname"]}',
                    )
                )
            self.codebuild_policy.append(
                iam.PolicyStatement(
                    actions=[
                        'cloudfront:CreateInvalidation',
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                        's3:Get*',
                        's3:Put*',
                        's3:List*',
                        'sts:AssumeRole',
                    ],
                    resources=[
                        f'arn:aws:s3:::{self.resource_prefix}-*',
                        f'arn:aws:s3:::{self.resource_prefix}*/*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                        f'arn:aws:iam::*:role/{resource_prefix}*',
                        f'arn:aws:cloudfront::*:distribution/*',
                    ],
                ),
            )

            self.set_db_migration_stage(
                target_env,
            )

            if target_env.get('internet_facing', True):
                self.set_cloudfront_stage(
                    target_env,
                )
            else:
                self.set_albfront_stage(target_env, repository_name)

        if self.node.try_get_context('git_release'):
            self.set_release_stage()

        Tags.of(self).add('Application', f'{resource_prefix}-{git_branch}')

    def validate_deployment_params(self, git_branch, resource_prefix, target_envs):
        if not bool(re.match(r'^[a-zA-Z0-9-_]+$', git_branch)):
            raise ValueError(
                f'Git branch {git_branch} name is created to use AWS resources.'
                f'It must match the pattern ^[a-zA-Z0-9-_]+$'
            )
        for env in target_envs:
            if not bool(re.match(r'^[a-zA-Z0-9-_]+$', env['envname'])):
                raise ValueError(
                    f'envname {env["envname"]} is created to use AWS resources. '
                    f'It must match the pattern ^[a-zA-Z0-9-_]+$'
                )
            if (
                env['account'] == self.account
                and env['region'] == self.region
                and env['envname'] == git_branch
            ):
                raise ValueError(
                    f'Seems like tooling account and deployment '
                    f'account are the same in the same region with the same envname and git_branch.'
                    f'Try a different envname than git_branch for it to work'
                )
            if (
                    env.get("internet_facing", True) not in [True, False]
                    or env.get("with_approval", False) not in [True, False]
                    or env.get("prod_sizing", False) not in [True, False]
                    or env.get("enable_cw_canaries", False) not in [True, False]
                    or env.get("enable_cw_rum", False) not in [True, False]
            ):
                raise ValueError(
                    f'Data type not supported in one of cdk.json variables (internet_facing,with_approvalprod_sizing,enable_cw_canaries,enable_cw_rum) \n'
                    f'Supported data type : Boolean'
                )
        if len(resource_prefix) >= 20:
            raise ValueError(
                f'Resource prefix {resource_prefix} '
                f'must be less than 50 characters to avoid AWS resources naming limits'
            )

    def set_quality_gate_stage(self):
        quality_gate_param = self.node.try_get_context('quality_gate')
        if quality_gate_param is not False:
            it_project_role = iam.Role(
                self,
                id=f'ItCobdeBuildRole{self.git_branch}',
                role_name=f'{self.resource_prefix}-{self.git_branch}-integration-tests-role',
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal('codebuild.amazonaws.com'),
                    iam.AccountPrincipal(self.account),
                ),
            )
            for policy in self.codebuild_policy:
                it_project_role.add_to_policy(policy)
            gate_quality_wave = self.pipeline.add_wave('QualityGate')
            gate_quality_wave.add_pre(
                pipelines.CodeBuildStep(
                    id='ValidateDBMigrations',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    ),
                    commands=[
                        'yum -y install shadow-utils wget && yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel',
                        f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                        f'export envname={self.git_branch}',
                        f'export schema_name=validation',
                        'python -m venv env',
                        '. env/bin/activate',
                        'make drop-tables',
                        'make upgrade-db',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                    security_groups=[self.codebuild_sg],
                ),
                pipelines.CodeBuildStep(
                    id='SecurityChecks',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    ),
                    commands=[
                        'yum -y install shadow-utils wget && yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel',
                        f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                        'pip install --upgrade pip',
                        "python -m venv env",
                        '. env/bin/activate',
                        'make check-security',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                ),
                pipelines.CodeBuildStep(
                    id='Lint',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    ),
                    commands=[
                        'pip install --upgrade pip',
                        'python -m venv env',
                        '. env/bin/activate',
                        'make lint',
                        'cd frontend',
                        'npm install',
                        'npm run lint',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                ),
            )
            gate_quality_wave.add_post(
                pipelines.CodeBuildStep(
                    id='IntegrationTests',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    ),
                    partial_build_spec=codebuild.BuildSpec.from_object(
                        dict(
                            version='0.2',
                            phases={
                                'build': {
                                    'commands': [
                                        'n 16.15.1',
                                        'set -eu',
                                        'yum -y install shadow-utils wget && yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel',
                                        f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                                        f'export envname={self.git_branch}',
                                        'python -m venv env',
                                        '. env/bin/activate',
                                        'make coverage',
                                    ]
                                },
                            },
                            reports={
                                'CoverageReport': {
                                    'files': ['cobertura.xml'],
                                    'base-directory': '$CODEBUILD_SRC_DIR',
                                    'file-format': 'COBERTURAXML',
                                }
                            },
                        )
                    ),
                    commands=[],
                    role=it_project_role,
                    vpc=self.vpc,
                    security_groups=[self.codebuild_sg],
                ),
                pipelines.CodeBuildStep(
                    id='UploadCodeToS3',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    ),
                    commands=[
                        'mkdir -p source_build',
                        'mv backend ./source_build/',
                        'cd source_build/ && zip -r ../source_build/source_build.zip *',
                        f'aws s3api put-object --bucket {self.pipeline_bucket.bucket_name}  --key source_build.zip --body source_build.zip',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                    security_groups=[self.codebuild_sg],
                ),
            )
        else:
            it_project_role = iam.Role(
                self,
                id=f'ItCobdeBuildRole{self.git_branch}',
                role_name=f'{self.resource_prefix}-{self.git_branch}-integration-tests-role',
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal('codebuild.amazonaws.com'),
                    iam.AccountPrincipal(self.account),
                ),
            )
            for policy in self.codebuild_policy:
                it_project_role.add_to_policy(policy)

            gate_quality_wave = self.pipeline.add_wave('UploadCodeToS3')
            gate_quality_wave.add_pre(
                pipelines.CodeBuildStep(
                    id='UploadCodeToS3',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    ),
                    commands=[
                        'mkdir -p source_build',
                        'mv backend ./source_build/',
                        'cd source_build/ && zip -r ../source_build/source_build.zip *',
                        f'aws s3api put-object --bucket {self.pipeline_bucket.bucket_name}  --key source_build.zip --body source_build.zip',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                    security_groups=[self.codebuild_sg],
                ),
            )


    def set_ecr_stage(
        self,
        target_env,
    ):
        repository_name = f"{self.resource_prefix}-{target_env['envname']}-repository"
        ecr_stage = self.pipeline.add_stage(
            ECRStage(
                self,
                f'{self.resource_prefix}-ecr-stage',
                env={
                    'account': target_env['account'],
                    'region': target_env['region'],
                },
                envname=target_env['envname'],
                tooling_account_id=self.account,
                target_envs=self.target_envs,
                repository_name=repository_name,
            )
        )
        ecr_stage.add_post(
            pipelines.CodeBuildStep(
                id='LambdaImage',
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    privileged=True,
                    environment_variables={
                        'REPOSITORY_URI': codebuild.BuildEnvironmentVariable(
                            value=f"{target_env['account']}.dkr.ecr.{target_env['region']}.amazonaws.com/{self.resource_prefix}-{target_env['envname']}-repository"
                        ),
                        'IMAGE_TAG': codebuild.BuildEnvironmentVariable(
                            value=f'lambdas-{self.image_tag}'
                        ),
                    },
                ),
                commands=[
                    'yum -y install shadow-utils wget && yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel',
                    f"make deploy-image type=lambda image-tag=$IMAGE_TAG account={target_env['account']} region={target_env['region']} repo={repository_name}",
                ],
                role_policy_statements=self.codebuild_policy,
                vpc=self.vpc,
            ),
            pipelines.CodeBuildStep(
                id='ECSImage',
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    privileged=True,
                    environment_variables={
                        'REPOSITORY_URI': codebuild.BuildEnvironmentVariable(
                            value=f"{target_env['account']}.dkr.ecr.{target_env['region']}.amazonaws.com/{repository_name}"
                        ),
                        'IMAGE_TAG': codebuild.BuildEnvironmentVariable(
                            value=f'cdkproxy-{self.image_tag}'
                        ),
                    },
                ),
                commands=[
                    'yum -y install shadow-utils wget && yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel',
                    f"make deploy-image type=ecs image-tag=$IMAGE_TAG account={target_env['account']} region={target_env['region']} repo={repository_name}",
                ],
                role_policy_statements=self.codebuild_policy,
                vpc=self.vpc,
            ),
        )
        return repository_name

    def set_backend_stage(self, target_env, repository_name):
        backend_stage = self.pipeline.add_stage(
            BackendStage(
                self,
                f"{self.resource_prefix}-{target_env['envname']}-backend-stage",
                env={
                    'account': target_env['account'],
                    'region': target_env['region'],
                },
                envname=target_env['envname'],
                resource_prefix=self.resource_prefix,
                tooling_account_id=self.account,
                pipeline_bucket=self.pipeline_bucket_name,
                ecr_repository=f'arn:aws:ecr:{target_env.get("region", self.region)}:{self.account}:repository/{repository_name}',
                commit_id=self.image_tag,
                vpc_id=target_env.get('vpc_id'),
                vpc_endpoints_sg=target_env.get('vpc_endpoints_sg'),
                internet_facing=target_env.get('internet_facing', True),
                custom_domain=target_env.get('custom_domain'),
                ip_ranges=target_env.get('ip_ranges'),
                apig_vpce=target_env.get('apig_vpce'),
                prod_sizing=target_env.get('prod_sizing', True),
                quicksight_enabled=target_env.get('enable_quicksight_monitoring', False),
                enable_cw_rum=target_env.get('enable_cw_rum', False),
                enable_cw_canaries=target_env.get('enable_cw_canaries', False),
                shared_dashboard_sessions=target_env.get('shared_dashboard_sessions', 'anonymous'),
            )
        )
        return backend_stage

    def set_db_migration_stage(
        self,
        target_env,
    ):
        migration_wave = self.pipeline.add_wave(
            f"{self.resource_prefix}-{target_env['envname']}-dbmigration-stage"
        )
        migration_wave.add_post(
            pipelines.CodeBuildStep(
                id='MigrateDB',
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                ),
                commands=[
                    'mkdir ~/.aws/ && touch ~/.aws/config',
                    'echo "[profile buildprofile]" > ~/.aws/config',
                    f'echo "role_arn = arn:aws:iam::{target_env["account"]}:role/{self.resource_prefix}-{target_env["envname"]}-cb-dbmigration-role" >> ~/.aws/config',
                    'echo "credential_source = EcsContainer" >> ~/.aws/config',
                    'aws sts get-caller-identity --profile buildprofile',
                    f'aws codebuild start-build --project-name {self.resource_prefix}-{target_env["envname"]}-dbmigration --profile buildprofile --region {target_env.get("region", self.region)} > codebuild-id.json',
                    f'aws codebuild batch-get-builds --ids $(jq -r .build.id codebuild-id.json) --profile buildprofile --region {target_env.get("region", self.region)} > codebuild-output.json',
                    f'while [ "$(jq -r .builds[0].buildStatus codebuild-output.json)" != "SUCCEEDED" ] && [ "$(jq -r .builds[0].buildStatus codebuild-output.json)" != "FAILED" ]; do echo "running migration"; aws codebuild batch-get-builds --ids $(jq -r .build.id codebuild-id.json) --profile buildprofile --region {target_env.get("region", self.region)} > codebuild-output.json; echo "$(jq -r .builds[0].buildStatus codebuild-output.json)"; sleep 5; done',
                    'if [ "$(jq -r .builds[0].buildStatus codebuild-output.json)" = "FAILED" ]; then echo "Failed";  cat codebuild-output.json; exit -1; fi',
                    'cat codebuild-output.json ',
                ],
                role_policy_statements=self.codebuild_policy,
                vpc=self.vpc,
            ),
        )

    def set_cloudfront_stage(self, target_env):
        cloudfront_stage = self.pipeline.add_stage(
            CloudfrontStage(
                self,
                f"{self.resource_prefix}-{target_env['envname']}-cloudfront-stage",
                env={
                    'account': target_env['account'],
                    'region': 'us-east-1',
                },
                envname=target_env['envname'],
                resource_prefix=self.resource_prefix,
                tooling_account_id=self.account,
                custom_domain=target_env.get('custom_domain'),
            )
        )
        front_stage_actions = (
            pipelines.CodeBuildStep(
                id='DeployFrontEnd',
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                    compute_type=codebuild.ComputeType.LARGE,
                ),
                install_commands=["n 14.18.3"],
                commands=[
                    f'export REACT_APP_STAGE={target_env["envname"]}',
                    f'export envname={target_env["envname"]}',
                    f'export internet_facing={target_env.get("internet_facing", True)}',
                    f'export custom_domain={str(True) if target_env.get("custom_domain") else str(False)}',
                    f'export deployment_region={target_env.get("region", self.region)}',
                    f'export enable_cw_rum={target_env.get("enable_cw_rum", False)}',
                    f'export resource_prefix={self.resource_prefix}',
                    'mkdir ~/.aws/ && touch ~/.aws/config',
                    'echo "[profile buildprofile]" > ~/.aws/config',
                    f'echo "role_arn = arn:aws:iam::{target_env["account"]}:role/{self.resource_prefix}-{target_env["envname"]}-S3DeploymentRole" >> ~/.aws/config',
                    'echo "credential_source = EcsContainer" >> ~/.aws/config',
                    'aws sts get-caller-identity --profile buildprofile',
                    'export AWS_PROFILE=buildprofile',
                    'pip install boto3==1.20.50',
                    'pip install beautifulsoup4',
                    'python deploy/configs/frontend_config.py',
                    'export AWS_DEFAULT_REGION=us-east-1',
                    f"export distributionId=$(aws ssm get-parameter --name /dataall/{target_env['envname']}/CloudfrontDistributionId --profile buildprofile --output text --query 'Parameter.Value')",
                    f"export bucket=$(aws ssm get-parameter --name /dataall/{target_env['envname']}/CloudfrontDistributionBucket --profile buildprofile --output text --query 'Parameter.Value')",
                    'export NODE_OPTIONS="--max-old-space-size=6144"',
                    'npm install -g yarn',
                    'cd frontend',
                    'yarn install',
                    'yarn build',
                    'aws s3 sync build/ s3://$bucket --profile buildprofile',
                    "aws cloudfront create-invalidation --distribution-id $distributionId --paths '/*' --profile buildprofile",
                ],
                role_policy_statements=self.codebuild_policy,
                vpc=self.vpc,
            ),
            self.cognito_config_action(target_env),
        )
        if target_env.get('enable_cw_rum', False):
            front_stage_actions = (
                *front_stage_actions,
                self.cw_rum_config_action(target_env),
            )
        self.pipeline.add_wave(
            f"{self.resource_prefix}-{target_env['envname']}-frontend-stage"
        ).add_post(*front_stage_actions)
        self.pipeline.add_wave(
            f"{self.resource_prefix}-{target_env['envname']}-docs-stage"
        ).add_post(
            pipelines.CodeBuildStep(
                id='UpdateDocumentation',
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                ),
                commands=[
                    f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                    f"make assume-role REMOTE_ACCOUNT_ID={target_env['account']} REMOTE_ROLE={self.resource_prefix}-{target_env['envname']}-S3DeploymentRole",
                    '. ./.env.assumed_role',
                    'aws sts get-caller-identity',
                    'export AWS_DEFAULT_REGION=us-east-1',
                    f"export distributionId=$(aws ssm get-parameter --name /dataall/{target_env['envname']}/cloudfront/docs/user/CloudfrontDistributionId --output text --query 'Parameter.Value')",
                    f"export bucket=$(aws ssm get-parameter --name /dataall/{target_env['envname']}/cloudfront/docs/user/CloudfrontDistributionBucket --output text --query 'Parameter.Value')",
                    'cd documentation/userguide',
                    'pip install -r requirements.txt',
                    'mkdocs build',
                    'aws s3 sync site/ s3://$bucket',
                    "aws cloudfront create-invalidation --distribution-id $distributionId --paths '/*'",
                ],
                role_policy_statements=self.codebuild_policy,
                vpc=self.vpc,
            ),
        )

    def cw_rum_config_action(self, target_env):
        return pipelines.CodeBuildStep(
            id='ConfigureRUM',
            build_environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
            ),
            commands=[
                f'export envname={target_env["envname"]}',
                f'export internet_facing={target_env.get("internet_facing", True)}',
                f'export custom_domain={str(True) if target_env.get("custom_domain") else str(False)}',
                f'export deployment_region={target_env.get("region", self.region)}',
                f'export resource_prefix={self.resource_prefix}',
                'mkdir ~/.aws/ && touch ~/.aws/config',
                'echo "[profile buildprofile]" > ~/.aws/config',
                f'echo "role_arn = arn:aws:iam::{target_env["account"]}:role/{self.resource_prefix}-{target_env["envname"]}-rum-config-role" >> ~/.aws/config',
                'echo "credential_source = EcsContainer" >> ~/.aws/config',
                'aws sts get-caller-identity --profile buildprofile',
                'export AWS_PROFILE=buildprofile',
                'pip install --upgrade pip',
                'pip install boto3==1.20.46',
                'python deploy/configs/rum_config.py',
            ],
            role_policy_statements=self.codebuild_policy,
            vpc=self.vpc,
        )

    def cognito_config_action(self, target_env):
        return pipelines.CodeBuildStep(
            id='ConfigureCognito',
            build_environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
            ),
            commands=[
                f'export envname={target_env["envname"]}',
                f'export resource_prefix={self.resource_prefix}',
                f'export internet_facing={target_env.get("internet_facing", True)}',
                f'export custom_domain={str(True) if target_env.get("custom_domain") else str(False)}',
                f'export deployment_region={target_env.get("region", self.region)}',
                f'export enable_cw_canaries={target_env.get("enable_cw_canaries", False)}',
                'mkdir ~/.aws/ && touch ~/.aws/config',
                'echo "[profile buildprofile]" > ~/.aws/config',
                f'echo "role_arn = arn:aws:iam::{target_env["account"]}:role/{self.resource_prefix}-{target_env["envname"]}-cognito-config-role" >> ~/.aws/config',
                'echo "credential_source = EcsContainer" >> ~/.aws/config',
                'aws sts get-caller-identity --profile buildprofile',
                'export AWS_PROFILE=buildprofile',
                'pip install --upgrade pip',
                'pip install boto3==1.20.46',
                'python deploy/configs/cognito_urls_config.py',
            ],
            role_policy_statements=self.codebuild_policy,
            vpc=self.vpc,
        )

    def set_albfront_stage(self, target_env, repository_name):
        albfront_stage = self.pipeline.add_stage(
            AlbFrontStage(
                self,
                f'{self.resource_prefix}-{target_env["envname"]}-albfront-stage',
                env={
                    'account': target_env['account'],
                    'region': target_env['region'],
                },
                envname=target_env['envname'],
                ecr_repository=f'arn:aws:ecr:{self.region}:{self.account}:repository/{repository_name}',
                image_tag=self.image_tag,
                custom_domain=target_env['custom_domain'],
                ip_ranges=target_env.get('ip_ranges'),
            ),
            pre=[
                pipelines.CodeBuildStep(
                    id='FrontendImage',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                        compute_type=codebuild.ComputeType.LARGE,
                        privileged=True,
                        environment_variables={
                            'REPOSITORY_URI': codebuild.BuildEnvironmentVariable(
                                value=f'{self.account}.dkr.ecr.{self.region}.amazonaws.com/{repository_name}'
                            ),
                            'IMAGE_TAG': codebuild.BuildEnvironmentVariable(
                                value=f'frontend-{self.image_tag}'
                            ),
                        },
                    ),
                    commands=[
                        f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                        f'export REACT_APP_STAGE={target_env["envname"]}',
                        f'export envname={target_env["envname"]}',
                        f'export internet_facing={target_env.get("internet_facing", False)}',
                        f'export custom_domain=True',
                        f'export deployment_region={target_env.get("region", self.region)}',
                        f'export enable_cw_rum={target_env.get("enable_cw_rum", False)}',
                        f'export resource_prefix={self.resource_prefix}',
                        'mkdir ~/.aws/ && touch ~/.aws/config',
                        'echo "[profile buildprofile]" > ~/.aws/config',
                        f'echo "role_arn = arn:aws:iam::{target_env["account"]}:role/{self.resource_prefix}-{target_env["envname"]}-cognito-config-role" >> ~/.aws/config',
                        'echo "credential_source = EcsContainer" >> ~/.aws/config',
                        'aws sts get-caller-identity --profile buildprofile',
                        'export AWS_PROFILE=buildprofile',
                        'pip install boto3==1.20.50',
                        'pip install beautifulsoup4',
                        'python deploy/configs/frontend_config.py',
                        'unset AWS_PROFILE',
                        'cd frontend',
                        f'docker build -f docker/prod/Dockerfile --build-arg REACT_APP_STAGE={target_env["envname"]} --build-arg DOMAIN={target_env.get("custom_domain", {}).get("name")} -t $IMAGE_TAG:$IMAGE_TAG .',
                        f'aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {self.account}.dkr.ecr.{self.region}.amazonaws.com',
                        'docker tag $IMAGE_TAG:$IMAGE_TAG $REPOSITORY_URI:$IMAGE_TAG',
                        'docker push $REPOSITORY_URI:$IMAGE_TAG',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                ),
                pipelines.CodeBuildStep(
                    id='UserGuideImage',
                    build_environment=codebuild.BuildEnvironment(
                        build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                        compute_type=codebuild.ComputeType.LARGE,
                        privileged=True,
                        environment_variables={
                            'REPOSITORY_URI': codebuild.BuildEnvironmentVariable(
                                value=f'{self.account}.dkr.ecr.{self.region}.amazonaws.com/{repository_name}'
                            ),
                            'IMAGE_TAG': codebuild.BuildEnvironmentVariable(
                                value=f'userguide-{self.image_tag}'
                            ),
                        },
                    ),
                    commands=[
                        f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                        'cd documentation/userguide',
                        'docker build -f docker/prod/Dockerfile -t $IMAGE_TAG:$IMAGE_TAG .',
                        f'aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {self.account}.dkr.ecr.{self.region}.amazonaws.com',
                        'docker tag $IMAGE_TAG:$IMAGE_TAG $REPOSITORY_URI:$IMAGE_TAG',
                        'docker push $REPOSITORY_URI:$IMAGE_TAG',
                    ],
                    role_policy_statements=self.codebuild_policy,
                    vpc=self.vpc,
                ),
            ],
            post=self.evaluate_post_albfront_stage(target_env)
        )

    def evaluate_post_albfront_stage(self, target_env):
        if target_env.get("enable_cw_rum", False):
            post=[
                self.cognito_config_action(target_env),
                self.cw_rum_config_action(target_env),
            ]
        else:
            post=[
                self.cognito_config_action(target_env),
            ]
        return post

    def set_release_stage(
        self,
    ):
        git_project_role = iam.Role(
            self,
            id=f'GitReleaseCBRole{self.git_branch}',
            role_name=f'{self.resource_prefix}-{self.git_branch}-git-release-role',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('codebuild.amazonaws.com'),
                iam.AccountPrincipal(self.account),
            ),
        )
        for policy in self.codebuild_policy:
            git_project_role.add_to_policy(policy)

        git_project_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'codecommit:CreateBranch',
                    'codecommit:GetCommit',
                    'codecommit:ListBranches',
                    'codecommit:GetRepository',
                    'codecommit:GetBranch',
                    'codecommit:GitPull',
                    'codecommit:PutFile',
                    'codecommit:CreateCommit',
                    'codecommit:GitPush',
                    'codecommit:ListTagsForResource',
                ],
                resources=[f'arn:aws:codecommit:{self.region}:{self.account}:dataall'],
            ),
        )
        self.pipeline.add_wave(
            f'{self.resource_prefix}-{self.git_branch}-release-stage'
        ).add_post(
            pipelines.CodeBuildStep(
                id='GitRelease',
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                ),
                partial_build_spec=codebuild.BuildSpec.from_object(
                    dict(
                        version='0.2',
                        phases={
                            'build': {
                                'commands': [
                                    'set -eu',
                                    f'aws codeartifact login --tool pip --repository {self.codeartifact.pip_repo.attr_name} --domain {self.codeartifact.domain.attr_name} --domain-owner {self.codeartifact.domain.attr_owner}',
                                    'python -m venv env',
                                    '. env/bin/activate',
                                    'pip install git-remote-codecommit',
                                    'mkdir release && cd release',
                                    f'git clone codecommit::{self.region}://dataall',
                                    'cd dataall',
                                    f'git checkout {self.git_branch}',
                                    f'make version-minor branch={self.git_branch}',
                                ]
                            },
                        },
                    )
                ),
                role=git_project_role,
                vpc=self.vpc,
                security_groups=[self.codebuild_sg],
                commands=[],
            )
        )
