from functools import cached_property
from pathlib import Path

from aws_cdk import aws_appsync
from aws_cdk import aws_logs
from aws_cdk.aws_cognito import IUserPool
from aws_cdk.aws_lambda import IFunction
from aws_cdk.aws_rds import ServerlessCluster
from awscdk.appsync_utils import CodeFirstSchema

from .pyNestedStack import pyNestedClass


class AppSyncStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname,
        resource_prefix,
        user_pool: IUserPool,
        api_handler: IFunction,
        cluster: ServerlessCluster,
        role,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self.user_pool = user_pool
        self.api_handler = api_handler
        self.cluster = cluster
        self.resolver_role = role

    @cached_property
    def schema(self) -> CodeFirstSchema:
        return CodeFirstSchema()

    @cached_property
    def api(self) -> aws_appsync.GraphqlApi:
        return aws_appsync.GraphqlApi(
            self,
            'Api',
            name='demo',
            log_config=aws_appsync.LogConfig(retention=aws_logs.RetentionDays.ONE_DAY),
            definition=aws_appsync.Definition.from_schema(self.schema),
            authorization_config=aws_appsync.AuthorizationConfig(
                default_authorization=aws_appsync.AuthorizationMode(
                    authorization_type=aws_appsync.AuthorizationType.USER_POOL,
                    user_pool_config=aws_appsync.UserPoolConfig(user_pool=self.user_pool),
                )
            ),
        )

    @cached_property
    def data_source(self) -> aws_appsync.LambdaDataSource:
        return aws_appsync.LambdaDataSource(
            self,
            'CommonLambdaDataSource',
            api=self.api,
            lambda_function=self.api_handler,
        )

    @cached_property
    def rds_data_source(self) -> aws_appsync.RdsDataSource:
        return aws_appsync.RdsDataSource(
            self,
            'CommonRDSDataSource',
            api=self.api,
            serverless_cluster=self.cluster,
            secret_store=self.cluster.secret,
            service_role=self.resolver_role,
            database_name=self.cluster._new_cfn_props.database_name,
        )

    @cached_property
    def data_source_func(self) -> aws_appsync.AppsyncFunction:
        return aws_appsync.AppsyncFunction(
            self,
            'CommonAppsyncFunction',
            api=self.api,
            data_source=self.data_source,
            code=aws_appsync.Code.from_asset(str(Path(__file__).parent.joinpath('schema/function_code.js'))),
            name='CommonAppsyncFunction',
            runtime=aws_appsync.FunctionRuntime.JS_1_0_0,
        )
