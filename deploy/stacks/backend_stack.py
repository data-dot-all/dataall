from builtins import super

from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ec2 as ec2
from aws_cdk import Stack

from .aurora import AuroraServerlessStack
from .cognito import IdpStack
from .container import ContainerStack
from .cw_canaries import CloudWatchCanariesStack
from .cw_rum import CloudWatchRumStack
from .dbmigration import DBMigrationStack
from .lambda_api import LambdaApiStack
from .monitoring import MonitoringStack
from .opensearch import OpenSearchStack
from .param_store_stack import ParamStoreStack
from .s3_resources import S3ResourcesStack
from .secrets_stack import SecretsManagerStack
from .sqs import SqsStack
from .vpc import VpcStack


class BackendStack(Stack):
    def __init__(
        self,
        scope,
        id,
        envname: str = 'dev',
        resource_prefix='dataall',
        tooling_account_id=None,
        ecr_repository=None,
        image_tag=None,
        pipeline_bucket=None,
        vpc_id=None,
        vpc_endpoints_sg=None,
        internet_facing=True,
        custom_domain=None,
        ip_ranges=None,
        apig_vpce=None,
        prod_sizing=False,
        quicksight_enabled=False,
        enable_cw_canaries=False,
        enable_cw_rum=False,
        shared_dashboard_sessions='anonymous',
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        vpc_stack = VpcStack(
            self,
            id='Vpc',
            envname=envname,
            resource_prefix=resource_prefix,
            vpc_endpoints_sg=vpc_endpoints_sg,
            vpc_id=vpc_id,
            **kwargs,
        )
        vpc = vpc_stack.vpc
        vpc_endpoints_sg = vpc_stack.vpce_security_group

        ParamStoreStack(
            self,
            f'ParamStore',
            envname=envname,
            resource_prefix=resource_prefix,
            custom_domain=custom_domain,
            enable_cw_canaries=enable_cw_canaries,
            quicksight_enabled=quicksight_enabled,
            shared_dashboard_sessions=shared_dashboard_sessions,
            **kwargs,
        )

        SecretsManagerStack(
            self,
            f'Secrets',
            envname=envname,
            resource_prefix=resource_prefix,
            enable_cw_canaries=enable_cw_canaries,
            **kwargs,
        )

        s3_resources_stack = S3ResourcesStack(
            self,
            f'S3Resources',
            envname=envname,
            resource_prefix=resource_prefix,
            **kwargs,
        )

        cognito_stack = IdpStack(
            self,
            f'Cognito',
            envname=envname,
            resource_prefix=resource_prefix,
            internet_facing=internet_facing,
            tooling_account_id=tooling_account_id,
            enable_cw_rum=enable_cw_rum,
            **kwargs,
        )

        sqs_stack = SqsStack(
            self,
            f'SqsStack',
            envname=envname,
            resource_prefix=resource_prefix,
            prod_sizing=prod_sizing,
            **kwargs,
        )

        repo = ecr.Repository.from_repository_arn(
            self, 'ECRREPO', repository_arn=ecr_repository
        )

        lambda_api_stack = LambdaApiStack(
            self,
            f'Lambdas',
            envname=envname,
            resource_prefix=resource_prefix,
            vpc=vpc,
            sqs_queue=sqs_stack.queue,
            image_tag=image_tag,
            ecr_repository=repo,
            internet_facing=internet_facing,
            ip_ranges=ip_ranges,
            apig_vpce=apig_vpce,
            prod_sizing=prod_sizing,
            user_pool=cognito_stack.user_pool,
            **kwargs,
        )

        ecs_stack = ContainerStack(
            self,
            f'ECS',
            envname=envname,
            resource_prefix=resource_prefix,
            vpc=vpc,
            vpc_endpoints_sg=vpc_endpoints_sg,
            ecr_repository=repo,
            image_tag=image_tag,
            prod_sizing=prod_sizing,
            **kwargs,
        )

        dbmigration_stack = DBMigrationStack(
            self,
            f'DbMigration',
            envname=envname,
            resource_prefix=resource_prefix,
            vpc=vpc,
            tooling_account_id=tooling_account_id,
            pipeline_bucket=pipeline_bucket,
            **kwargs,
        )

        if quicksight_enabled:
            pivot_role_in_account = iam.Role(
                self,
                id=f'PivotRoleLimited',
                role_name=f'dataallPivotRole',
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal('lambda.amazonaws.com'),
                    iam.AccountPrincipal(self.account),
                ),
            )

            pivot_role_in_account_policies = [
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                        'ssm:PutParameter'
                    ],
                    resources=[f'arn:aws:ssm:*:{self.account}:parameter/dataall*']
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'secretsmanager:DescribeSecret',
                        'secretsmanager:GetSecretValue'
                    ],
                    resources=[f'arn:aws:secretsmanager:*:{self.account}:secret:dataall*']
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'ssm:DescribeParameters',
                        'quicksight:GetSessionEmbedUrl',
                        'quicksight:ListUserGroups',
                        'secretsmanager:ListSecrets'
                    ],
                    resources=['*']
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'quicksight:RegisterUser',
                        'quicksight:DescribeUser',
                        'quicksight:DescribeGroup',
                        'quicksight:CreateGroup',
                        'quicksight:CreateGroupMembership',
                        'quicksight:UpdateUser',
                        'quicksight:CreateDataSource',
                        'quicksight:DescribeDataSource',
                        'quicksight:PassDataSource',
                        'quicksight:GetDashboardEmbedUrl',
                        'quicksight:DescribeDashboardPermissions',
                        'quicksight:SearchDashboards',
                        'quicksight:GetAuthCode',
                        'quicksight:CreateDataSet'
                    ],
                    resources=[f'arn:aws:quicksight:*:{self.account}:user/*',
                               f'arn:aws:quicksight:*:{self.account}:group/*',
                               f'arn:aws:quicksight:*:{self.account}:datasource/*',
                               f'arn:aws:quicksight:*:{self.account}:dashboard/*',
                               f'arn:aws:quicksight:*:{self.account}:dataset/*'
                               ],
                )
            ]

            for policy in pivot_role_in_account_policies:
                pivot_role_in_account.add_to_policy(policy)

            quicksight_monitoring_sg = ec2.SecurityGroup(
                self,
                f'QuicksightMonitoringDBSG{envname}',
                security_group_name=f'{resource_prefix}-{envname}-quicksight-monitoring-sg',
                vpc=vpc,
                allow_all_outbound=False,
            )

        else:
            quicksight_monitoring_sg = None

        aurora_stack = AuroraServerlessStack(
            self,
            f'Aurora',
            envname=envname,
            resource_prefix=resource_prefix,
            vpc=vpc,
            lambdas=[
                lambda_api_stack.aws_handler,
                lambda_api_stack.api_handler,
            ],
            ecs_security_groups=ecs_stack.ecs_security_groups,
            codebuild_dbmigration_sg=dbmigration_stack.codebuild_sg,
            prod_sizing=prod_sizing,
            quicksight_monitoring_sg=quicksight_monitoring_sg,
            **kwargs,
        )

        opensearch_stack = OpenSearchStack(
            self,
            f'OpenSearch',
            envname=envname,
            resource_prefix=resource_prefix,
            vpc=vpc,
            lambdas=[
                lambda_api_stack.aws_handler,
                lambda_api_stack.api_handler,
                lambda_api_stack.elasticsearch_proxy_handler,
            ],
            ecs_security_groups=ecs_stack.ecs_security_groups,
            prod_sizing=prod_sizing,
            **kwargs,
        )

        monitoring_stack = MonitoringStack(
            self,
            f'CWDashboards',
            envname=envname,
            resource_prefix=resource_prefix,
            lambdas=[
                lambda_api_stack.aws_handler,
                lambda_api_stack.api_handler,
                lambda_api_stack.elasticsearch_proxy_handler,
            ],
            database=aurora_stack.cluster.cluster_identifier,
            ecs_cluster=ecs_stack.ecs_cluster,
            ecs_task_definitions=ecs_stack.ecs_task_definitions,
            backend_api=lambda_api_stack.backend_api_name,
            opensearch_domain=opensearch_stack.domain.domain_name,
            queue_name=sqs_stack.queue.queue_name,
            **kwargs,
        )

        if enable_cw_rum:
            CloudWatchRumStack(
                self,
                'CWRumStack',
                envname=envname,
                resource_prefix=resource_prefix,
                tooling_account_id=tooling_account_id,
                cw_alarm_action=monitoring_stack.cw_alarm_action,
                cognito_identity_pool_id=cognito_stack.identity_pool.ref,
                cognito_identity_pool_role_arn=cognito_stack.identity_pool_role.role_arn,
                custom_domain_name=custom_domain.get('hosted_zone_name')
                if custom_domain
                else None,
            )

        if enable_cw_canaries:
            CloudWatchCanariesStack(
                self,
                'CWCanariesStack',
                envname=envname,
                resource_prefix=resource_prefix,
                vpc=vpc,
                logs_bucket=s3_resources_stack.logs_bucket,
                cw_alarm_action=monitoring_stack.cw_alarm_action,
                internet_facing=internet_facing,
            )
