from aws_cdk import aws_appsync
from aws_cdk import aws_logs
from aws_cdk.aws_cognito import IUserPool
from aws_cdk.aws_lambda import IFunction
from awscdk.appsync_utils import CodeFirstSchema
from injector import singleton, Module, provider

from .pyNestedStack import pyNestedClass
from .schema import create_schema


class AppSyncStack(pyNestedClass, Module):
    def __init__(self, scope, id, user_pool: IUserPool, api_handler: IFunction, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.user_pool = user_pool
        self.api_handler = api_handler
        create_schema([self])

    @singleton
    @provider
    def api(self) -> aws_appsync.GraphqlApi:
        return aws_appsync.GraphqlApi(
            self,
            "Api",
            name="demo",
            log_config=aws_appsync.LogConfig(
                retention=aws_logs.RetentionDays.ONE_DAY
            ),
            definition=aws_appsync.Definition.from_schema(CodeFirstSchema()),
            authorization_config=aws_appsync.AuthorizationConfig(
                default_authorization=aws_appsync.AuthorizationMode(
                    authorization_type=aws_appsync.AuthorizationType.USER_POOL,
                    user_pool_config=aws_appsync.UserPoolConfig(user_pool=self.user_pool)
                )
            )
        )

    @singleton
    @provider
    def data_source(self, api: aws_appsync.GraphqlApi) -> aws_appsync.LambdaDataSource:
        return aws_appsync.LambdaDataSource(
            self,
            'CommonLambdaDataSource',
            api=api,
            lambda_function=self.api_handler,
        )
