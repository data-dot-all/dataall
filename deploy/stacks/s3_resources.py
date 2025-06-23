import os

from aws_cdk import (
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_s3_deployment as s3d,
    RemovalPolicy,
    CfnOutput,
)

from .cdk_asset_trail import setup_cdk_asset_trail
from .pyNestedStack import pyNestedClass


class S3ResourcesStack(pyNestedClass):
    def __init__(self, scope, id, envname='dev', resource_prefix='dataall', **kwargs):
        super().__init__(scope, id, **kwargs)

        self.logs_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-access-logs',
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            versioned=True,
            auto_delete_objects=True,
        )
        setup_cdk_asset_trail(self, self.logs_bucket)

        self.bucket_name = f'{resource_prefix}-{envname}-{self.account}-{self.region}-resources'
        self.bucket = s3.Bucket(
            self,
            f'ResourcesBucket{envname}',
            bucket_name=f'{resource_prefix}-{envname}-{self.account}-{self.region}-resources',
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_bucket=s3.Bucket.from_bucket_name(
                self, 'AccessLogsBucket', self.logs_bucket.bucket_name
            ),
            server_access_logs_prefix=f'access_logs/{self.bucket_name}',
            versioned=True,
            auto_delete_objects=True,
        )

        ssm.StringParameter(
            self,
            f'S3ResourcesBucketParam{envname}',
            parameter_name=f'/dataall/{envname}/s3/resources_bucket_name',
            string_value=self.bucket.bucket_name,
        )

        pivot_role = os.path.realpath(os.path.abspath(os.path.join(__file__, '..', '..', 'pivot_role')))

        cdk_exec_policy = os.path.realpath(os.path.abspath(os.path.join(__file__, '..', '..', 'cdk_exec_policy')))

        s3d.BucketDeployment(
            self,
            f'PivotRoleDeployment{envname}',
            sources=[s3d.Source.asset(pivot_role)],
            destination_bucket=self.bucket,
            destination_key_prefix='roles',
        )

        ssm.StringParameter(
            self,
            f'S3ResourcesBucketKeyParam{envname}',
            parameter_name=f'/dataall/{envname}/s3/pivot_role_prefix',
            string_value='roles/pivotRole.yaml',
        )

        s3d.BucketDeployment(
            self,
            f'CDKExecutionPolicyDeployment{envname}',
            sources=[s3d.Source.asset(cdk_exec_policy)],
            destination_bucket=self.bucket,
            destination_key_prefix='policies',
        )

        ssm.StringParameter(
            self,
            f'S3ResourcesBucketKeyParamCDK{envname}',
            parameter_name=f'/dataall/{envname}/s3/cdk_exec_policy_prefix',
            string_value='policies/cdkExecPolicy.yaml',
        )

        CfnOutput(
            self,
            f'{resource_prefix}-{envname}-resources-bucket-output',
            export_name=f'{resource_prefix}-{envname}-resources-bucket',
            value=self.bucket.bucket_name,
            description=f'{resource_prefix}-{envname}-resources-bucket',
        )

        CfnOutput(
            self,
            f'{resource_prefix}-{envname}-access-logs-bucket-name',
            export_name=f'{resource_prefix}-{envname}-access-logs-bucket-name',
            value=self.bucket.bucket_name,
            description=f'DO NOT USE {resource_prefix}-{envname}-access-logs-bucket-name',
        )

        CfnOutput(
            self,
            f'{resource_prefix}-{envname}-access-logs-bucket',
            export_name=f'{resource_prefix}-{envname}-access-logs-bucket',
            value=self.logs_bucket.bucket_name,
            description=f'{resource_prefix}-{envname}-access-logs-bucket',
        )
