import json

from aws_cdk import (
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda_destinations as lambda_destination,
    aws_wafv2 as wafv2,
    aws_ssm as ssm,
    aws_sns as sns,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_sqs as sqs,
    aws_logs as logs,
    Duration,
    CfnOutput,
    Fn,
    RemovalPolicy,
)
from aws_cdk.aws_ec2 import (
    InterfaceVpcEndpoint,
    InterfaceVpcEndpointAwsService,
    Port,
    Peer,
)

from .pyNestedStack import pyNestedClass

class LambdaApiStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        vpc=None,
        sqs_queue: sqs.Queue = None,
        ecr_repository=None,
        image_tag=None,
        internet_facing=True,
        custom_waf_rules=None,
        ip_ranges=None,
        apig_vpce=None,
        prod_sizing=False,
        user_pool=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        if self.node.try_get_context('image_tag'):
            image_tag = self.node.try_get_context('image_tag')

        image_tag = f'lambdas-{image_tag}'

        self.esproxy_dlq = self.set_dlq(f'{resource_prefix}-{envname}-esproxy-dlq')
        self.elasticsearch_proxy_handler = _lambda.DockerImageFunction(
            self,
            'ElasticSearchProxyHandler',
            function_name=f'{resource_prefix}-{envname}-esproxy',
            description='dataall es search function',
            role=self.create_function_role(envname, resource_prefix, 'esproxy'),
            code=_lambda.DockerImageCode.from_ecr(
                repository=ecr_repository, tag=image_tag, cmd=['search_handler.handler']
            ),
            vpc=vpc,
            memory_size=1664 if prod_sizing else 256,
            timeout=Duration.minutes(15),
            environment={'envname': envname, 'LOG_LEVEL': 'INFO'},
            dead_letter_queue_enabled=True,
            dead_letter_queue=self.esproxy_dlq,
            on_failure=lambda_destination.SqsDestination(self.esproxy_dlq),
            tracing=_lambda.Tracing.ACTIVE,
        )

        self.api_handler_dlq = self.set_dlq(f'{resource_prefix}-{envname}-graphql-dlq')
        self.api_handler = _lambda.DockerImageFunction(
            self,
            'LambdaGraphQL',
            function_name=f'{resource_prefix}-{envname}-graphql',
            description='dataall graphql function',
            role=self.create_function_role(envname, resource_prefix, 'graphql'),
            code=_lambda.DockerImageCode.from_ecr(
                repository=ecr_repository, tag=image_tag, cmd=['api_handler.handler']
            ),
            vpc=vpc,
            memory_size=3008 if prod_sizing else 1024,
            timeout=Duration.minutes(15),
            environment={'envname': envname, 'LOG_LEVEL': 'INFO'},
            dead_letter_queue_enabled=True,
            dead_letter_queue=self.api_handler_dlq,
            on_failure=lambda_destination.SqsDestination(self.api_handler_dlq),
            tracing=_lambda.Tracing.ACTIVE,
        )

        self.aws_handler_dlq = self.set_dlq(
            f'{resource_prefix}-{envname}-awsworker-dlq'
        )
        self.aws_handler = _lambda.DockerImageFunction(
            self,
            'AWSWorker',
            function_name=f'{resource_prefix}-{envname}-awsworker',
            description='dataall aws worker for aws asynchronous tasks function',
            role=self.create_function_role(envname, resource_prefix, 'awsworker'),
            code=_lambda.DockerImageCode.from_ecr(
                repository=ecr_repository, tag=image_tag, cmd=['aws_handler.handler']
            ),
            environment={'envname': envname, 'LOG_LEVEL': 'INFO'},
            memory_size=1664 if prod_sizing else 256,
            timeout=Duration.minutes(15),
            vpc=vpc,
            dead_letter_queue_enabled=True,
            dead_letter_queue=self.aws_handler_dlq,
            on_failure=lambda_destination.SqsDestination(self.aws_handler_dlq),
            tracing=_lambda.Tracing.ACTIVE,
        )
        self.aws_handler.add_event_source(
            lambda_event_sources.SqsEventSource(
                queue=sqs_queue,
                batch_size=1,
            )
        )

        self.backend_api_name = f'{resource_prefix}-{envname}-api'

        self.graphql_api, self.acl = self.create_api_gateway(
            apig_vpce,
            envname,
            internet_facing,
            custom_waf_rules,
            ip_ranges,
            resource_prefix,
            vpc,
            user_pool,
        )

        self.create_sns_topic(
            envname=envname,
            construct_id='BackendTopic',
            lambda_function=self.api_handler,
            param_name='backend_sns_topic_arn',
            topic_name=f'{resource_prefix}-{envname}-backend-topic',
        )

    def create_function_role(self, envname, resource_prefix, fn_name):

        role_name = f'{resource_prefix}-{envname}-{fn_name}-role'

        role_inline_policy = iam.Policy(
            self,
            f'{resource_prefix}-{envname}-{fn_name}-policy',
            policy_name=f'{resource_prefix}-{envname}-{fn_name}-policy',
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'secretsmanager:GetSecretValue',
                        'kms:Decrypt',
                        'secretsmanager:DescribeSecret',
                        'ecs:RunTask',
                        'kms:Encrypt',
                        'sqs:ReceiveMessage',
                        'kms:GenerateDataKey',
                        'sqs:SendMessage',
                        'ecs:DescribeClusters',
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                    ],
                    resources=[
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                        f'arn:aws:ecs:{self.region}:{self.account}:cluster/*{resource_prefix}*',
                        f'arn:aws:ecs:{self.region}:{self.account}:task-definition/*{resource_prefix}*:*',
                        f'arn:aws:kms:{self.region}:{self.account}:key/*',
                        f'arn:aws:sqs:{self.region}:{self.account}:*{resource_prefix}*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'sts:AssumeRole',
                    ],
                    resources=[
                        f"arn:aws:iam::*:role/{self.node.try_get_context('pivot_role_name') or 'dataallPivotRole'}"
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'ecs:ListTasks',
                    ],
                    resources=['*'],
                    conditions={
                        'ArnEquals': {
                            'ecs:cluster': f'arn:aws:ecs:{self.region}:{self.account}:cluster/*{resource_prefix}*'
                        }
                    },
                ),
                iam.PolicyStatement(
                    actions=[
                        'iam:PassRole',
                    ],
                    resources=[
                        f'arn:aws:iam::{self.account}:role/{resource_prefix}-{envname}*'
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        's3:GetObject',
                        's3:ListBucketVersions',
                        's3:ListBucket',
                        's3:GetBucketLocation',
                        's3:GetObjectVersion',
                        'logs:StartQuery',
                        'logs:DescribeLogGroups',
                        'logs:DescribeLogStreams',
                    ],
                    resources=[
                        f'arn:aws:s3:::{resource_prefix}-{envname}-{self.account}-{self.region}-resources/*',
                        f'arn:aws:s3:::{resource_prefix}-{envname}-{self.account}-{self.region}-resources',
                        f'arn:aws:logs:{self.region}:{self.account}:log-group:*{resource_prefix}*:log-stream:*',
                        f'arn:aws:logs:{self.region}:{self.account}:log-group:*{resource_prefix}*',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'logs:DescribeQueries',
                        'logs:StopQuery',
                        'logs:GetQueryResults',
                        'logs:CreateLogGroup',
                        'logs:CreateLogStream',
                        'logs:PutLogEvents',
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
                        'cognito-idp:ListGroups'
                    ],
                    resources=['*'],
                ),
            ],
        )
        role = iam.Role(
            self,
            role_name,
            role_name=role_name,
            inline_policies={
                f'{resource_prefix}-{envname}-{fn_name}-inline': role_inline_policy.document
            },
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        )
        return role

    def create_api_gateway(
        self,
        apig_vpce,
        envname,
        internet_facing,
        custom_waf_rules,
        ip_ranges,
        resource_prefix,
        vpc,
        user_pool,
    ):

        api_deploy_options = apigw.StageOptions(
            throttling_rate_limit=10000,
            throttling_burst_limit=5000,
            logging_level=apigw.MethodLoggingLevel.INFO,
            tracing_enabled=True,
            data_trace_enabled=True,
            metrics_enabled=True,
        )

        graphql_api = self.set_up_graphql_api_gateway(
            api_deploy_options,
            self.api_handler,
            self.backend_api_name,
            self.elasticsearch_proxy_handler,
            envname,
            internet_facing,
            vpc,
            ip_ranges,
            apig_vpce,
            resource_prefix,
            user_pool,
        )

        # Create IP set if IP filtering enabled in CDK.json
        ip_set_regional=None
        if custom_waf_rules and custom_waf_rules.get("allowed_ip_list"):
            ip_set_regional = wafv2.CfnIPSet(
                self,
                "DataallRegionalIPSet",
                name=f"{resource_prefix}-{envname}-ipset-regional",
                description=f"IP addresses allowed for Dataall {envname}",
                addresses=custom_waf_rules.get("allowed_ip_list"),
                ip_address_version="IPV4",
                scope="REGIONAL"
            )

        acl = wafv2.CfnWebACL(
            self,
            'ACL-ApiGW',
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope='REGIONAL',
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name='waf-apigw',
                sampled_requests_enabled=True,
            ),
            rules=self.get_waf_rules(envname,custom_waf_rules,ip_set_regional),
        )

        wafv2.CfnWebACLAssociation(
            self,
            'WafApiGW',
            resource_arn=f'arn:aws:apigateway:{self.region}::'
            f'/restapis/{graphql_api.rest_api_id}/stages/{graphql_api.deployment_stage.stage_name}',
            web_acl_arn=acl.get_att('Arn').to_string(),
        )

        CfnOutput(
            self,
            f'WebAclId{envname}',
            export_name=f'{resource_prefix}-{envname}-api-webacl',
            value=Fn.select(0, Fn.split('|', Fn.ref(acl.logical_id))),
        )
        CfnOutput(self, f'Url{envname}', value=graphql_api.url)

        return graphql_api, acl

    def set_up_graphql_api_gateway(
        self,
        api_deploy_options,
        api_handler,
        backend_api_name,
        elasticsearch_proxy_handler,
        envname,
        internet_facing,
        vpc: ec2.Vpc,
        ip_ranges,
        apig_vpce,
        resource_prefix,
        user_pool,
    ):
        cognito_authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            'CognitoAuthorizer',
            cognito_user_pools=[user_pool],
            authorizer_name=f'{resource_prefix}-{envname}-cognito-authorizer',
            identity_source='method.request.header.Authorization',
            results_cache_ttl=Duration.minutes(60),
        )
        if not internet_facing:
            if apig_vpce:
                api_vpc_endpoint = (
                    InterfaceVpcEndpoint.from_interface_vpc_endpoint_attributes(
                        self,
                        f'APIVpcEndpoint{envname}',
                        vpc_endpoint_id=apig_vpce,
                        port=443,
                    )
                )
            else:
                api_vpc_endpoint = InterfaceVpcEndpoint(
                    self,
                    f'APIVpcEndpoint{envname}',
                    vpc=vpc,
                    service=InterfaceVpcEndpointAwsService.APIGATEWAY,
                    private_dns_enabled=True,
                )
                api_vpc_endpoint.connections.allow_from(
                    Peer.ipv4(vpc.vpc_cidr_block), Port.tcp(443), 'Allow inbound HTTPS'
                )

            api_vpc_endpoint_id = api_vpc_endpoint.vpc_endpoint_id
            api_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        principals=[iam.AnyPrincipal()],
                        actions=['execute-api:Invoke'],
                        resources=['execute-api:/*'],
                        effect=iam.Effect.DENY,
                        conditions={
                            'StringNotEquals': {'aws:SourceVpce': api_vpc_endpoint_id}
                        },
                    ),
                    iam.PolicyStatement(
                        principals=[iam.AnyPrincipal()],
                        actions=['execute-api:Invoke'],
                        resources=['execute-api:/*'],
                        effect=iam.Effect.ALLOW,
                    ),
                ]
            )
            gw = apigw.RestApi(
                self,
                backend_api_name,
                rest_api_name=backend_api_name,
                deploy_options=api_deploy_options,
                endpoint_configuration=apigw.EndpointConfiguration(
                    types=[apigw.EndpointType.PRIVATE], vpc_endpoints=[api_vpc_endpoint]
                ),
                policy=api_policy,
            )
        else:
            gw = apigw.RestApi(
                self,
                backend_api_name,
                rest_api_name=backend_api_name,
                deploy_options=api_deploy_options,
            )
        api_url = gw.url
        integration = apigw.LambdaIntegration(api_handler)
        request_validator = apigw.RequestValidator(
            self,
            f'{resource_prefix}-{envname}-api-validator',
            rest_api=gw,
            validate_request_body=True,
        )
        graphql_validation_model = apigw.Model(
            self,
            'GraphQLValidationModel',
            rest_api=gw,
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title='GraphQL',
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    'operationName': apigw.JsonSchema(
                        type=apigw.JsonSchemaType.STRING,
                        description='GraphQL Operation name',
                    ),
                    'query': apigw.JsonSchema(
                        type=apigw.JsonSchemaType.STRING,
                        description='GraphQL operation body',
                    ),
                    'variables': apigw.JsonSchema(
                        type=apigw.JsonSchemaType.OBJECT,
                        description='GraphQL operation variables',
                    ),
                },
                required=['operationName', 'query', 'variables'],
            ),
        )
        ssm.StringParameter(
            self,
            'BackendApi',
            parameter_name=f'/dataall/{envname}/apiGateway/backendUrl',
            string_value=api_url,
        )
        graphql = gw.root.add_resource(path_part='graphql')
        graphql_proxy = graphql.add_resource(
            path_part='{proxy+}',
            default_integration=integration,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_headers=['*'],
            ),
        )
        graphql_proxy.add_method(
            'POST',
            authorizer=cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=request_validator,
            request_models={'application/json': graphql_validation_model},
        )
        search_integration = apigw.LambdaIntegration(elasticsearch_proxy_handler)
        search = gw.root.add_resource(path_part='search')
        search_validation_model = apigw.Model(
            self,
            'SearchValidationModel',
            rest_api=gw,
            schema=apigw.JsonSchema(
                schema=apigw.JsonSchemaVersion.DRAFT4,
                title='SearchAPI',
                type=apigw.JsonSchemaType.OBJECT,
                properties={
                    'preference': apigw.JsonSchema(
                        type=apigw.JsonSchemaType.STRING,
                        description='Search Preference',
                    ),
                    'query': apigw.JsonSchema(
                        type=apigw.JsonSchemaType.OBJECT,
                        description='Search Query',
                    ),
                },
                required=['preference', 'query'],
            ),
        )
        search_proxy = search.add_resource(
            path_part='{proxy+}',
            default_integration=search_integration,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_headers=['*'],
            ),
        )
        search_proxy.add_method(
            'POST',
            authorizer=cognito_authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=request_validator,
            request_models={'application/json': search_validation_model},
        )

        apigateway_log_group = logs.LogGroup(
            self,
            f'{resource_prefix}/{envname}/apigateway',
            log_group_name=f'{resource_prefix}/{envname}/apigateway',
            removal_policy=RemovalPolicy.DESTROY,
        )

        iam_policy = iam.PolicyDocument(
            assign_sids=True,
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'logs:CreateLogStream',
                        'logs:PutLogEvents',
                        'logs:DescribeLogGroups',
                        'logs:DescribeLogStreams',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[apigateway_log_group.log_group_arn],
                )
            ],
        )

        iam.Role(
            self,
            f'{resource_prefix}-{envname}-apigatewaylogs-role',
            assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'),
            inline_policies={
                f'{resource_prefix}-{envname}-apigateway-policy': iam_policy
            },
        )
        stage: apigw.CfnStage = gw.deployment_stage.node.default_child
        stage.access_log_setting = apigw.CfnStage.AccessLogSettingProperty(
            destination_arn=apigateway_log_group.log_group_arn,
            format=json.dumps(
                {
                    'requestId': '$context.requestId',
                    'userAgent': '$context.identity.userAgent',
                    'sourceIp': '$context.identity.sourceIp',
                    'requestTime': '$context.requestTime',
                    'requestTimeEpoch': '$context.requestTimeEpoch',
                    'httpMethod': '$context.httpMethod',
                    'path': '$context.path',
                    'status': '$context.status',
                    'protocol': '$context.protocol',
                    'responseLength': '$context.responseLength',
                    'domainName': '$context.domainName',
                }
            ),
        )
        return gw

    @staticmethod
    def get_api_resource_policy(vpc, ip_ranges):
        statements = [
            iam.PolicyStatement(
                principals=[iam.AnyPrincipal()],
                actions=['execute-api:Invoke'],
                resources=['execute-api:/*'],
                effect=iam.Effect.DENY,
                conditions={'NotIpAddress': {'aws:VpcSourceIp': vpc.vpc_cidr_block}},
            ),
            iam.PolicyStatement(
                principals=[iam.AnyPrincipal()],
                actions=['execute-api:Invoke'],
                resources=['execute-api:/*'],
                effect=iam.Effect.ALLOW,
            ),
        ]
        if ip_ranges:
            statements.append(
                iam.PolicyStatement(
                    principals=[iam.AnyPrincipal()],
                    actions=['execute-api:Invoke'],
                    resources=['execute-api:/*'],
                    effect=iam.Effect.DENY,
                    conditions={'NotIpAddress': {'aws:SourceIp': ip_ranges}},
                )
            )
        api_policy = iam.PolicyDocument(statements=statements)
        return api_policy

    @staticmethod
    def get_waf_rules(envname,custom_waf_rules=None,ip_set_regional=None):
        waf_rules = []
        priority = 0
        if custom_waf_rules:
            if custom_waf_rules.get("allowed_geo_list"):
                waf_rules.append(
                    wafv2.CfnWebACL.RuleProperty(
                        name='GeoMatch',
                        statement=wafv2.CfnWebACL.StatementProperty(
                            not_statement=wafv2.CfnWebACL.NotStatementProperty(
                                statement=wafv2.CfnWebACL.StatementProperty(
                                    geo_match_statement=wafv2.CfnWebACL.GeoMatchStatementProperty(
                                        country_codes=custom_waf_rules.get("allowed_geo_list")
                                    )
                                )
                            )
                        ),
                        action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            sampled_requests_enabled=True,
                            cloud_watch_metrics_enabled=True,
                            metric_name='GeoMatch',
                        ),
                        priority=priority,
                    )
                )
                priority += 1
            if custom_waf_rules.get("allowed_ip_list"):
                waf_rules.append(
                    wafv2.CfnWebACL.RuleProperty(
                        name='IPMatch',
                        statement=wafv2.CfnWebACL.StatementProperty(
                            not_statement=wafv2.CfnWebACL.NotStatementProperty(
                                statement=wafv2.CfnWebACL.StatementProperty(
                                    ip_set_reference_statement={
                                        "arn" : ip_set_regional.attr_arn
                                    }
                                )
                            )
                        ),
                        action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            sampled_requests_enabled=True,
                            cloud_watch_metrics_enabled=True,
                            metric_name='IPMatch',
                        ),
                        priority=priority,
                    )
                )
                priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='AWS-AWSManagedRulesAdminProtectionRuleSet',
                statement=wafv2.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name='AWS', name='AWSManagedRulesAdminProtectionRuleSet'
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name='AWS-AWSManagedRulesAdminProtectionRuleSet',
                ),
                priority=priority,
                override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            )
        )
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='AWS-AWSManagedRulesAmazonIpReputationList',
                statement=wafv2.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name='AWS', name='AWSManagedRulesAmazonIpReputationList'
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name='AWS-AWSManagedRulesAmazonIpReputationList',
                ),
                priority=priority,
                override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            )
        )
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='AWS-AWSManagedRulesCommonRuleSet',
                statement=wafv2.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name='AWS', name='AWSManagedRulesCommonRuleSet'
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name='AWS-AWSManagedRulesCommonRuleSet',
                ),
                priority=priority,
                override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            )
        )
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='AWS-AWSManagedRulesKnownBadInputsRuleSet',
                statement=wafv2.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name='AWS', name='AWSManagedRulesKnownBadInputsRuleSet'
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name='AWS-AWSManagedRulesKnownBadInputsRuleSet',
                ),
                priority=priority,
                override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            )
        )
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='AWS-AWSManagedRulesLinuxRuleSet',
                statement=wafv2.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name='AWS', name='AWSManagedRulesLinuxRuleSet'
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name='AWS-AWSManagedRulesLinuxRuleSet',
                ),
                priority=priority,
                override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            )
        )
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='AWS-AWSManagedRulesSQLiRuleSet',
                statement=wafv2.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name='AWS', name='AWSManagedRulesSQLiRuleSet'
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name='AWS-AWSManagedRulesSQLiRuleSet',
                ),
                priority=priority,
                override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            )
        )
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name='APIGatewayRateLimit',
                statement=wafv2.CfnWebACL.StatementProperty(
                    rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                        aggregate_key_type='IP', limit=1000
                    )
                ),
                action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name=f'WAFAPIGatewayRateLimit{envname}',
                ),
                priority=priority,
            )
        )
        priority += 1
        return waf_rules

    def create_sns_topic(
        self, construct_id, envname, lambda_function, param_name, topic_name=None
    ):
        key = kms.Key(
            self,
            topic_name,
            removal_policy=RemovalPolicy.DESTROY,
            alias=topic_name,
            enable_key_rotation=True,
        )
        topic = sns.Topic(self, construct_id, topic_name=topic_name, master_key=key)
        ssm.StringParameter(
            self,
            f'{construct_id}Parameter',
            parameter_name=f'/dataall/{envname}/sns_topics/{param_name}',
            string_value=topic.topic_arn,
        )
        service_principal_name = 'sns.amazonaws.com'
        lambda_function.add_permission(
            f'{construct_id}Permission',
            action='lambda:InvokeFunction',
            principal=iam.ServicePrincipal(service_principal_name),
            source_arn=topic.topic_arn,
        )
        sns.Subscription(
            self,
            f'{construct_id}Subscription',
            protocol=sns.SubscriptionProtocol.LAMBDA,
            topic=topic,
            endpoint=lambda_function.function_arn,
        )
        return topic

    def set_dlq(self, queue_name) -> sqs.Queue:
        queue_key = kms.Key(
            self,
            f'{queue_name}-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{queue_name}-key',
            enable_key_rotation=True,
        )

        dlq = sqs.Queue(
            self,
            f'{queue_name}-queue',
            queue_name=f'{queue_name}',
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=queue_key,
            data_key_reuse=Duration.days(1),
            removal_policy=RemovalPolicy.DESTROY,
        )

        enforce_tls_statement = iam.PolicyStatement(
            sid='Enforce TLS for all principals',
            effect=iam.Effect.DENY,
            principals=[
                iam.AnyPrincipal(),
            ],
            actions=[
                'sqs:*',
            ],
            resources=[dlq.queue_arn],
            conditions={
                'Bool': {'aws:SecureTransport': 'false'},
            },
        )

        dlq.add_to_resource_policy(enforce_tls_statement)
        return dlq
