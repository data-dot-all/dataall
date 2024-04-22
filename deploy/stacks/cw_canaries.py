import os

from aws_cdk import (
    aws_synthetics as synthetics,
    aws_cloudwatch as cw,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy,
)

from .pyNestedStack import pyNestedClass


class CloudWatchCanariesStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        logs_bucket: s3.Bucket = None,
        cw_alarm_action=None,
        internet_facing=True,
        vpc: ec2.Vpc = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..',
                'canaries',
                'python',
                'canary.py',
            ),
            'r',
        ) as canary_module:
            script = canary_module.read()

        self.bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-canaries',
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_bucket=s3.Bucket.from_bucket_name(self, 'AccessLogsBucket', logs_bucket.bucket_name),
            server_access_logs_prefix=f'access_logs/{resource_prefix}-{envname}-canaries',
            versioned=True,
            auto_delete_objects=True,
        )

        canary_role = self.create_canary_role(envname, resource_prefix, self.bucket)

        canary_sg: ec2.SecurityGroup = ec2.SecurityGroup(
            self,
            f'{resource_prefix}-{envname}-canary-sg',
            security_group_name=f'{resource_prefix}-{envname}-canary-sg',
            vpc=vpc,
            allow_all_outbound=True,
        )

        schedule = synthetics.CfnCanary.ScheduleProperty(expression='rate(1 hour)')

        vpc_config = synthetics.CfnCanary.VPCConfigProperty(
            vpc_id=vpc.vpc_id,
            subnet_ids=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT, one_per_az=True).subnet_ids,
            security_group_ids=[canary_sg.security_group_id],
        )
        canary_name = f'{resource_prefix[:6]}-{envname}-canary'

        synthetics.CfnCanary(
            self,
            f'{resource_prefix}-{envname}-canary',
            name=canary_name,
            code=synthetics.CfnCanary.CodeProperty(
                handler='canary.handler',
                script=script,
            ),
            execution_role_arn=canary_role.role_arn,
            artifact_s3_location=f's3://{self.bucket.bucket_name}/canaries',
            runtime_version='syn-python-selenium-1.0',
            schedule=schedule,
            start_canary_after_creation=False,
            vpc_config=vpc_config,
            run_config=synthetics.CfnCanary.RunConfigProperty(
                environment_variables={
                    'envname': envname,
                    'resource_prefix': resource_prefix,
                    'internet_facing': str(internet_facing),
                },
                timeout_in_seconds=840,
            ),
        )

        metric = cw.Metric(
            namespace='CloudWatchSynthetics',
            metric_name='SuccessPercent',
            dimensions_map=dict(CanaryName=canary_name),
            period=Duration.hours(1),
            statistic='Sum',
        )

        alarm = cw.Alarm(
            self,
            f'{resource_prefix}-{envname}-canary-alarm',
            alarm_name=f'{canary_name}-error-alarm',
            metric=metric,
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            alarm_description=f'Synthetics alarm metric: Failed {canary_name}',
            comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.IGNORE,
        )
        alarm.add_alarm_action(cw_alarm_action)

    def create_canary_role(self, envname, resource_prefix, s3_bucket):
        role_inline_policy = iam.Policy(
            self,
            f'{resource_prefix}-{envname}-canary-policy',
            policy_name=f'{resource_prefix}-{envname}-canary-policy',
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                    ],
                    resources=[
                        f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'secretsmanager:GetSecretValue',
                        'secretsmanager:DescribeSecret',
                    ],
                    resources=[
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        's3:ListAllMyBuckets',
                        'logs:CreateLogStream',
                        'logs:CreateLogGroup',
                        'logs:PutLogEvents',
                        'kms:Decrypt',
                        'kms:GenerateDataKey',
                        'ec2:CreateNetworkInterface',
                        'ec2:DescribeNetworkInterfaces',
                        'ec2:DeleteNetworkInterface',
                        'ec2:AssignPrivateIpAddresses',
                        'ec2:UnassignPrivateIpAddresses',
                        'xray:PutTraceSegments',
                        'xray:PutTelemetryRecords',
                        'xray:GetSamplingRules',
                        'xray:GetSamplingTargets',
                        'xray:GetSamplingStatisticSummaries',
                    ],
                    resources=['*'],
                ),
                iam.PolicyStatement(
                    actions=['cloudwatch:PutMetricData'],
                    resources=['*'],
                    conditions={'StringEquals': {'cloudwatch:namespace': 'CloudWatchSynthetics'}},
                ),
                iam.PolicyStatement(
                    actions=[
                        's3:GetBucketLocation',
                    ],
                    resources=[s3_bucket.bucket_arn],
                ),
                iam.PolicyStatement(
                    actions=[
                        's3:PutObject',
                    ],
                    resources=[f'{s3_bucket.bucket_arn}/canaries/*'],
                ),
            ],
        )
        canary_role = iam.Role(
            self,
            f'{resource_prefix}-{envname}-canary-role',
            inline_policies={f'CanaryRoleInlinePolicy{envname}': role_inline_policy.document},
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        )
        return canary_role
