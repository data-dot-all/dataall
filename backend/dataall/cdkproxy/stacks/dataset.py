import logging
import os

from aws_cdk import (
    custom_resources as cr,
    aws_s3 as s3,
    aws_kms as kms,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_glue as glue,
    Stack,
    Duration,
    CfnResource,
    CustomResource,
    Tags,
)
from aws_cdk.aws_glue import CfnCrawler

from .manager import stack
from ... import db
from ...aws.handlers.lakeformation import LakeFormation
from ...aws.handlers.quicksight import Quicksight
from ...aws.handlers.sts import SessionHelper
from ...db import models
from ...db.api import Environment
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack(stack='dataset')
class Dataset(Stack):
    """Deploy common dataset resources:
            - dataset S3 Bucket + KMS key (If S3 Bucket not imported)
            - dataset IAM role
            - custom resource to create glue database and grant permissions
            - custom resource to register S3 location in LF
            - Glue crawler
            - Glue profiling job
    """
    module_name = __file__

    def get_engine(self) -> db.Engine:
        envname = os.environ.get('envname', 'local')
        engine = db.get_engine(envname=envname)
        return engine

    def get_env(self, dataset) -> models.Environment:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = session.query(models.Environment).get(dataset.environmentUri)
        return env

    def get_env_group(self, dataset) -> models.EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(
                session, dataset.SamlAdminGroupName, dataset.environmentUri
            )
        return env

    def get_target_with_uri(self, target_uri) -> models.Dataset:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            dataset = session.query(models.Dataset).get(target_uri)
            if not dataset:
                raise Exception('ObjectNotFound')
        return dataset

    def get_target(self) -> models.Dataset:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            dataset = session.query(models.Dataset).get(self.target_uri)
            if not dataset:
                raise Exception('ObjectNotFound')
        return dataset

    def __init__(self, scope, id, target_uri: str = None, **kwargs):
        super().__init__(
            scope,
            id,
            description="Cloud formation stack of DATASET: {}; URI: {}; DESCRIPTION: {}".format(
                self.get_target_with_uri(target_uri=target_uri).label,
                target_uri,
                self.get_target_with_uri(target_uri=target_uri).description,
            )[:1024],
            **kwargs)

        # Read input
        self.target_uri = target_uri
        self.pivot_role_name = SessionHelper.get_delegation_role_name()
        dataset = self.get_target()
        env = self.get_env(dataset)
        env_group = self.get_env_group(dataset)

        quicksight_default_group_arn = None
        if env.dashboardsEnabled:
            quicksight_default_group = Quicksight.create_quicksight_group(AwsAccountId=env.AwsAccountId)
            quicksight_default_group_arn = quicksight_default_group['Group']['Arn']

        # Dataset S3 Bucket and KMS key
        dataset_key = False
        if dataset.imported and dataset.importedS3Bucket:
            dataset_bucket = s3.Bucket.from_bucket_name(
                self, f'ImportedBucket{dataset.datasetUri}', dataset.S3BucketName
            )
            if dataset.importedKmsKey:
                dataset_key = kms.Key.from_lookup(
                    self, f'ImportedKey{dataset.datasetUri}', alias_name=f"alias/{dataset.KmsAlias}"
                )
        else:
            dataset_key = kms.Key(
                self,
                'DatasetKmsKey',
                alias=dataset.KmsAlias,
                enable_key_rotation=True,
                policy=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            sid="EnableDatasetOwnerKeyUsage",
                            resources=['*'],
                            effect=iam.Effect.ALLOW,
                            principals=[
                                iam.ArnPrincipal(env_group.environmentIAMRoleArn),
                            ],
                            actions=[
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:ReEncrypt*",
                                "kms:GenerateDataKey*",
                                "kms:DescribeKey",
                                "kms:List*",
                                "kms:GetKeyPolicy",
                            ],
                        ),
                        iam.PolicyStatement(
                            sid='KMSPivotRolePermissions',
                            effect=iam.Effect.ALLOW,
                            actions=[
                                'kms:Decrypt',
                                'kms:Encrypt',
                                'kms:GenerateDataKey*',
                                'kms:PutKeyPolicy',
                                "kms:GetKeyPolicy",
                                'kms:ReEncrypt*',
                                'kms:TagResource',
                                'kms:UntagResource',
                                'kms:DeleteAlias',
                                'kms:DescribeKey',
                                'kms:CreateAlias',
                                'kms:List*',
                            ],
                            resources=['*'],
                            principals=[
                                iam.ArnPrincipal(f'arn:aws:iam::{env.AwsAccountId}:role/{self.pivot_role_name}')
                            ],
                        )
                    ]
                ),
                admins=[
                    iam.ArnPrincipal(env.CDKRoleArn),
                ]
            )

            dataset_bucket = s3.Bucket(
                self,
                'DatasetBucket',
                bucket_name=dataset.S3BucketName,
                encryption=s3.BucketEncryption.KMS,
                encryption_key=dataset_key,
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
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                server_access_logs_bucket=s3.Bucket.from_bucket_name(
                    self,
                    'EnvAccessLogsBucket',
                    f'{env.EnvironmentDefaultBucketName}',
                ),
                server_access_logs_prefix=f'access_logs/{dataset.S3BucketName}/',
                enforce_ssl=True,
                versioned=True,
                bucket_key_enabled=True,
            )

            dataset_bucket.add_lifecycle_rule(
                abort_incomplete_multipart_upload_after=Duration.days(7),
                noncurrent_version_transitions=[
                    s3.NoncurrentVersionTransition(
                        storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                        transition_after=Duration.days(30),
                    ),
                    s3.NoncurrentVersionTransition(
                        storage_class=s3.StorageClass.GLACIER,
                        transition_after=Duration.days(60),
                    ),
                ],
                transitions=[
                    s3.Transition(
                        storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                        transition_after=Duration.days(90),
                    ),
                    s3.Transition(
                        storage_class=s3.StorageClass.GLACIER,
                        transition_after=Duration.days(360),
                    ),
                ],
                enabled=True,
            )

        # Dataset IAM role - ETL policies
        dataset_admin_policy = iam.Policy(
            self,
            'DatasetAdminPolicy',
            policy_name=dataset.S3BucketName,
            statements=[
                iam.PolicyStatement(
                    sid="ListAll",
                    actions=[
                        "s3:ListAllMyBuckets",
                        "s3:ListAccessPoints",
                    ],
                    resources=["*"],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    sid="ListDatasetBucket",
                    actions=[
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    resources=[dataset_bucket.bucket_arn],
                    effect=iam.Effect.ALLOW,
                ),
                iam.PolicyStatement(
                    sid="ReadWriteDatasetBucket",
                    actions=[
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:GetObjectVersion",
                        "s3:DeleteObject"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[dataset_bucket.bucket_arn + '/*'],
                ),
                iam.PolicyStatement(
                    sid="ReadAccessPointsDatasetBucket",
                    actions=[
                        's3:GetAccessPoint',
                        's3:GetAccessPointPolicy',
                        's3:GetAccessPointPolicyStatus',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{dataset.datasetUri}*',
                    ],
                ),
                iam.PolicyStatement(
                    sid="GlueAccessCrawler",
                    actions=[
                        "glue:Get*",
                        "glue:BatchGet*",
                        "glue:CreateTable",
                        "glue:UpdateTable",
                        "glue:DeleteTableVersion",
                        "glue:DeleteTable",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:glue:*:{dataset.AwsAccountId}:catalog",
                        f"arn:aws:glue:{dataset.region}:{dataset.AwsAccountId}:database/default",
                        f"arn:aws:glue:{dataset.region}:{dataset.AwsAccountId}:database/{dataset.GlueDatabaseName}",
                        f"arn:aws:glue:{dataset.region}:{dataset.AwsAccountId}:table/{dataset.GlueDatabaseName}/*"
                    ]
                ),
                iam.PolicyStatement(
                    sid="GlueAccessDefault",
                    actions=[
                        "glue:GetDatabase",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:glue:{dataset.region}:{dataset.AwsAccountId}:database/default",
                    ]
                ),
                iam.PolicyStatement(
                    sid="CreateLoggingGlueCrawler",
                    actions=[
                        'logs:CreateLogGroup',
                        'logs:CreateLogStream',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f'arn:aws:logs:{dataset.region}:{dataset.AwsAccountId}:log-group:/aws-glue/crawlers*',
                    ],
                ),
                iam.PolicyStatement(
                    sid="LoggingGlueCrawler",
                    actions=[
                        'logs:PutLogEvents',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f'arn:aws:logs:{dataset.region}:{dataset.AwsAccountId}:log-group:/aws-glue/crawlers:log-stream:{dataset.GlueCrawlerName}',
                    ],
                ),
                iam.PolicyStatement(
                    actions=['s3:ListBucket'],
                    resources=[f'arn:aws:s3:::{env.EnvironmentDefaultBucketName}'],
                    effect=iam.Effect.ALLOW
                ),
                iam.PolicyStatement(
                    sid="ReadEnvironmentBucketProfiling",
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:GetObjectVersion"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[f'arn:aws:s3:::{env.EnvironmentDefaultBucketName}/profiling/code/*'],
                ),
                iam.PolicyStatement(
                    sid="ReadWriteEnvironmentBucketProfiling",
                    actions=[
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:GetObjectVersion",
                        "s3:DeleteObject"
                    ],
                    resources=[f'arn:aws:s3:::{env.EnvironmentDefaultBucketName}/profiling/results/{dataset.datasetUri}/*'],
                    effect=iam.Effect.ALLOW,
                ),
            ],
        )
        if dataset_key:
            dataset_admin_policy.add_statements(
                iam.PolicyStatement(
                    sid="KMSAccess",
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:GenerateDataKey"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[dataset_key.key_arn],
                )
            )
        dataset_admin_policy.node.add_dependency(dataset_bucket)

        dataset_admin_role = iam.Role(
            self,
            'DatasetAdminRole',
            role_name=dataset.IAMDatasetAdminRoleArn.split('/')[-1],
            assumed_by=iam.CompositePrincipal(
                iam.ArnPrincipal(
                    f'arn:aws:iam::{dataset.AwsAccountId}:role/{self.pivot_role_name}'
                ),
                iam.ServicePrincipal('glue.amazonaws.com'),
            ),
        )
        dataset_admin_policy.attach_to_role(dataset_admin_role)

        # Add Key Policy For Users
        if not dataset.imported:
            dataset_key.add_to_resource_policy(
                iam.PolicyStatement(
                    sid="EnableDatasetIAMRoleKeyUsage",
                    resources=['*'],
                    effect=iam.Effect.ALLOW,
                    principals=[dataset_admin_role],
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                )
            )

        # Datalake location custom resource: registers the S3 location in LakeFormation
        registered_location = LakeFormation.check_existing_lf_registered_location(
            resource_arn=f'arn:aws:s3:::{dataset.S3BucketName}',
            role_arn=dataset.IAMDatasetAdminRoleArn,
            accountid=env.AwsAccountId,
            region=env.region
        )

        if not registered_location:
            storage_location = CfnResource(
                self,
                'DatasetStorageLocation',
                type='AWS::LakeFormation::Resource',
                properties={
                    'ResourceArn': f'arn:aws:s3:::{dataset.S3BucketName}',
                    'RoleArn': dataset.IAMDatasetAdminRoleArn,
                    'UseServiceLinkedRole': False,
                },
            )

        # Define dataset admin groups (those with data access grant)
        dataset_admins = [
            dataset_admin_role.role_arn,
            f'arn:aws:iam::{env.AwsAccountId}:role/{self.pivot_role_name}',
            env_group.environmentIAMRoleArn,
        ]
        if quicksight_default_group_arn:
            dataset_admins.append(quicksight_default_group_arn)

        # Get the Provider service token from SSM, the Lambda and Provider are created as part of the environment stack
        glue_db_provider_service_token = ssm.StringParameter.from_string_parameter_name(
            self,
            'GlueDatabaseProviderServiceToken',
            string_parameter_name=f'/dataall/{dataset.environmentUri}/cfn/custom-resources/gluehandler/provider/servicetoken',
        )

        glue_db = CustomResource(
            self,
            f'{env.resourcePrefix}GlueDatabaseCustomResource',
            service_token=glue_db_provider_service_token.string_value,
            resource_type='Custom::GlueDatabase',
            properties={
                'CatalogId': dataset.AwsAccountId,
                'DatabaseInput': {
                    'Description': 'dataall database {} '.format(
                        dataset.GlueDatabaseName
                    ),
                    'LocationUri': f's3://{dataset.S3BucketName}/',
                    'Name': f'{dataset.GlueDatabaseName}',
                    'CreateTableDefaultPermissions': [],
                    'Imported': 'IMPORTED-' if dataset.imported else ''
                },
                'DatabaseAdministrators': dataset_admins
            },
        )

        # Support resources: GlueCrawler for the dataset, Profiling Job and Trigger
        crawler = glue.CfnCrawler(
            self,
            dataset.GlueCrawlerName,
            description=f'datall Glue Crawler for bucket {dataset.S3BucketName}',
            name=dataset.GlueCrawlerName,
            database_name=dataset.GlueDatabaseName,
            schedule={'scheduleExpression': f'{dataset.GlueCrawlerSchedule}'}
            if dataset.GlueCrawlerSchedule
            else None,
            role=dataset_admin_role.role_arn,
            targets=CfnCrawler.TargetsProperty(
                s3_targets=[
                    CfnCrawler.S3TargetProperty(path=f's3://{dataset.S3BucketName}')
                ]
            ),
        )
        crawler.node.add_dependency(dataset_bucket)

        job_args = {
            '--additional-python-modules': 'urllib3<2,pydeequ',
            '--datasetUri': dataset.datasetUri,
            '--database': dataset.GlueDatabaseName,
            '--datasetRegion': dataset.region,
            '--dataallRegion': os.getenv('AWS_REGION', 'eu-west-1'),
            '--environmentUri': env.environmentUri,
            '--environmentBucket': env.EnvironmentDefaultBucketName,
            '--datasetBucket': dataset.S3BucketName,
            '--apiUrl': 'None',
            '--snsTopicArn': 'None',
            '--extra-jars': (
                f's3://{env.EnvironmentDefaultBucketName}'
                f'/profiling/code/jars/deequ-2.0.0-spark-3.1.jar'
            ),
            '--enable-metrics': 'true',
            '--enable-continuous-cloudwatch-log': 'true',
            '--enable-glue-datacatalog': 'true',
        }

        job = glue.CfnJob(
            self,
            'DatasetGlueProfilingJob',
            name=dataset.GlueProfilingJobName,
            role=dataset_admin_role.role_arn,
            allocated_capacity=10,
            execution_property=glue.CfnJob.ExecutionPropertyProperty(
                max_concurrent_runs=100
            ),
            command=glue.CfnJob.JobCommandProperty(
                name='glueetl',
                python_version='3',
                script_location=(
                    f's3://{env.EnvironmentDefaultBucketName}'
                    f'/profiling/code/glue_script.py'
                ),
            ),
            default_arguments=job_args,
            glue_version='3.0',
            tags={'Application': 'dataall'},
        )
        if dataset.GlueProfilingTriggerSchedule:
            trigger = glue.CfnTrigger(
                self,
                'DatasetGlueProfilingTrigger',
                name=dataset.GlueProfilingTriggerName,
                type='SCHEDULED',
                schedule=dataset.GlueProfilingTriggerSchedule,
                start_on_creation=True,
                actions=[
                    glue.CfnTrigger.ActionProperty(
                        job_name=dataset.GlueProfilingJobName, arguments=job_args
                    )
                ],
            )
            trigger.node.add_dependency(job)

        Tags.of(self).add('Classification', dataset.confidentiality)

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)
