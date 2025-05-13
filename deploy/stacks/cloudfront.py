import os

from aws_cdk import (
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_wafv2 as wafv2,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    CfnOutput,
    BundlingOptions,
    Fn,
)

from .cdk_asset_trail import setup_cdk_asset_trail
from .pyNestedStack import pyNestedClass
from .solution_bundling import SolutionBundling
from .waf_rules import get_waf_rules
from .iam_utils import get_tooling_account_external_id


class CloudfrontDistro(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        auth_at_edge=None,
        custom_domain=None,
        custom_waf_rules=None,
        tooling_account_id=None,
        custom_auth=None,
        backend_region=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.server_access_logs_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-cloudfront-access-logs',
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            versioned=True,
            auto_delete_objects=True,
        )

        """
        In case cloudfront (always us-east-1) and backend are in different regions create a trail in us-east-1 
        """
        if self.region != backend_region:
            setup_cdk_asset_trail(self, self.server_access_logs_bucket)

        # Create IP set if IP filtering enabled
        ip_set_cloudfront = None
        if custom_waf_rules and custom_waf_rules.get('allowed_ip_list'):
            ip_set_cloudfront = wafv2.CfnIPSet(
                self,
                'DataallCloudfrontIPSet',
                name=f'{resource_prefix}-{envname}-ipset-cloudfront',
                description=f'IP addresses to allow for Dataall {envname}',
                addresses=custom_waf_rules.get('allowed_ip_list'),
                ip_address_version='IPV4',
                scope='CLOUDFRONT',
            )

        acl = wafv2.CfnWebACL(
            self,
            'ACL-Cloudfront',
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope='CLOUDFRONT',
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name='waf-cloudfront',
                sampled_requests_enabled=True,
            ),
            rules=get_waf_rules(envname, 'Cloudfront', custom_waf_rules, ip_set_cloudfront),
        )

        logging_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-logging',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            server_access_logs_bucket=self.server_access_logs_bucket,
            server_access_logs_prefix=f'{resource_prefix}-{envname}-logging',
        )

        frontend_alternate_domain = None
        userguide_alternate_domain = None

        frontend_domain_names = None
        userguide_domain_names = None

        certificate = None
        ssl_support_method = None
        security_policy = None

        cloudfront_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-frontend',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            server_access_logs_bucket=self.server_access_logs_bucket,
            server_access_logs_prefix=f'{resource_prefix}-{envname}-frontend',
        )

        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, 'OriginAccessIdentity', comment='Allows Read-Access from CloudFront'
        )

        cloudfront_bucket.grant_read(origin_access_identity)

        if custom_domain and custom_domain['hosted_zone_name']:
            custom_domain_name = custom_domain['hosted_zone_name']
            hosted_zone_id = custom_domain['hosted_zone_id']

            frontend_alternate_domain = custom_domain_name
            userguide_alternate_domain = 'userguide.' + custom_domain_name

            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
                self,
                'CustomDomainHostedZone',
                hosted_zone_id=hosted_zone_id,
                zone_name=custom_domain_name,
            )

            if custom_domain.get('certificate_arn'):
                certificate = acm.Certificate.from_certificate_arn(
                    self, 'CustomDomainCertificate', custom_domain.get('certificate_arn')
                )
            else:
                certificate = acm.Certificate(
                    self,
                    'CustomDomainCertificate',
                    domain_name=custom_domain_name,
                    subject_alternative_names=[f'*.{custom_domain_name}'],
                    validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
                )

            frontend_domain_names = [frontend_alternate_domain]
            userguide_domain_names = [userguide_alternate_domain]
            ssl_support_method = cloudfront.SSLMethod.SNI
            security_policy = cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021

        cloudfront_distribution = cloudfront.Distribution(
            self,
            'CloudFrontDistribution',
            certificate=certificate,
            domain_names=frontend_domain_names,
            ssl_support_method=ssl_support_method,
            minimum_protocol_version=security_policy,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket=cloudfront_bucket, origin_access_identity=origin_access_identity),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object='index.html',
            error_responses=self.error_responses(),
            web_acl_id=acl.get_att('Arn').to_string(),
            log_bucket=logging_bucket,
            log_file_prefix='cloudfront-logs/frontend',
        )

        ssm_distribution_id = ssm.StringParameter(
            self,
            f'SSMDistribution{envname}',
            parameter_name=f'/dataall/{envname}/CloudfrontDistributionId',
            string_value=cloudfront_distribution.distribution_id,
        )
        ssm_distribution_domain_name = ssm.StringParameter(
            self,
            f'SSMDomainName{envname}',
            parameter_name=f'/dataall/{envname}/CloudfrontDistributionDomainName',
            string_value=cloudfront_distribution.distribution_domain_name,
        )
        ssm_distribution_bucket = ssm.StringParameter(
            self,
            f'SSMDistributionBucket{envname}',
            parameter_name=f'/dataall/{envname}/CloudfrontDistributionBucket',
            string_value=cloudfront_bucket.bucket_name,
        )
        cloudfront_resources = [
            f'arn:aws:cloudfront::{self.account}:distribution/{cloudfront_distribution.distribution_id}'
        ]
        self.user_docs_bucket = None
        if custom_auth is None:
            userguide_docs_distribution, user_docs_bucket, ssm_distribution_domain_name_userguide = (
                self.build_static_site(
                    'userguide',
                    acl,
                    auth_at_edge,
                    envname,
                    resource_prefix,
                    userguide_domain_names,
                    certificate,
                    ssl_support_method,
                    security_policy,
                    logging_bucket,
                )
            )

            self.userguide_docs_distribution = userguide_docs_distribution
            self.user_docs_bucket = user_docs_bucket
            cloudfront_resources += [
                f'arn:aws:cloudfront::{self.account}:distribution/{userguide_docs_distribution.distribution_id}'
            ]

            if userguide_alternate_domain:
                route53.ARecord(
                    self,
                    'CloudFrontUserguideDomain',
                    record_name=userguide_alternate_domain,
                    zone=hosted_zone,
                    target=route53.RecordTarget.from_alias(
                        route53_targets.CloudFrontTarget(userguide_docs_distribution)
                    ),
                )

        if frontend_alternate_domain:
            frontend_record = route53.ARecord(
                self,
                'CloudFrontFrontendDomain',
                record_name=frontend_alternate_domain,
                zone=hosted_zone,
                target=route53.RecordTarget.from_alias(route53_targets.CloudFrontTarget(cloudfront_distribution)),
            )

        if tooling_account_id:
            cross_account_deployment_role = iam.Role(
                self,
                f'S3DeploymentRole{envname}',
                role_name=f'{resource_prefix}-{envname}-S3DeploymentRole',
                assumed_by=iam.AccountPrincipal(tooling_account_id),
                external_ids=[get_tooling_account_external_id(self.account)],
            )
            resources_for_cross_account = []
            resources_for_cross_account.append(f'{cloudfront_bucket.bucket_arn}/*')
            if self.user_docs_bucket is not None:
                resources_for_cross_account.append(f'{self.user_docs_bucket.bucket_arn}/*')
            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        's3:Get*',
                        's3:Put*',
                    ],
                    resources=resources_for_cross_account,
                )
            )
            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=['s3:List*'],
                    resources=['*'],
                )
            )

            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(actions=['cloudfront:CreateInvalidation'], resources=cloudfront_resources)
            )

            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        'ssm:GetParameterHistory',
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                    ],
                    resources=[
                        f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                    ],
                )
            )
            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        'rum:GetAppMonitor',
                    ],
                    resources=[f'arn:aws:rum:*:{self.account}:appmonitor/*{resource_prefix}*'],
                )
            )

        CfnOutput(
            self,
            'OutputCfnFrontDistribution',
            export_name=f'OutputCfnFrontDistribution{envname}',
            value=cloudfront_distribution.distribution_id,
        )
        CfnOutput(
            self,
            'OutputCfnFrontDistributionDomainName',
            export_name=f'OutputCfnFrontDistributionDomainName{envname}',
            value=cloudfront_distribution.distribution_domain_name,
        )
        CfnOutput(
            self,
            'OutputCfnFrontDistributionBucket',
            export_name=f'OutputCfnFrontDistributionBucket{envname}',
            value=cloudfront_bucket.bucket_name,
        )

        self.frontend_distribution = cloudfront_distribution
        self.frontend_bucket = cloudfront_bucket
        self.cross_account_deployment_role = (
            cross_account_deployment_role.role_name if cross_account_deployment_role else None
        )

    def build_docs_http_headers(self, docs_http_headers, envname, resource_prefix):
        http_header_func = _lambda.Function(
            self,
            f'{resource_prefix}-{envname}-httpheaders-redirection',
            description='Edge function to set security policy headers for docs',
            handler='index.handler',
            code=_lambda.Code.from_asset(
                path=docs_http_headers,
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                    local=SolutionBundling(source_path=docs_http_headers),
                    command=['bash', '-c', """cp -au . /asset-output"""],
                ),
            ),
            timeout=Duration.seconds(5),
            memory_size=128,
            role=iam.Role(
                self,
                id=f'DocsHttpHeaders{envname}Role',
                role_name=f'{resource_prefix}-{envname}-httpheaders-role',
                managed_policies=[
                    iam.ManagedPolicy.from_managed_policy_arn(
                        self,
                        id=f'DocsHttpHeaders{envname}Policy',
                        managed_policy_arn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    )
                ],
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal('edgelambda.amazonaws.com'),
                    iam.ServicePrincipal('lambda.amazonaws.com'),
                ),
            ),
            runtime=_lambda.Runtime.NODEJS_18_X,
            logging_format=_lambda.LoggingFormat.JSON,
        )

        http_header_func_version = http_header_func.current_version

        return http_header_func, http_header_func_version

    def build_static_site(
        self,
        construct_id,
        acl,
        auth_at_edge,
        envname,
        resource_prefix,
        domain_names,
        certificate,
        ssl_support_method,
        security_policy,
        logging_bucket,
    ):
        # Lambda@edge for http_header_redirection
        docs_http_headers = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                'custom_resources',
                'docs_http_headers',
            )
        )

        if not os.path.isdir(docs_http_headers):
            raise Exception(f'Http Docs Headers Folder not found at {docs_http_headers}')

        (
            self.http_header_func,
            self.http_header_func_version,
        ) = self.build_docs_http_headers(docs_http_headers, envname, resource_prefix)

        parse = auth_at_edge.devdoc_app.get_att('Outputs.ParseAuthHandler').to_string()
        refresh = auth_at_edge.devdoc_app.get_att('Outputs.RefreshAuthHandler').to_string()
        signout = auth_at_edge.devdoc_app.get_att('Outputs.SignOutHandler').to_string()
        check = auth_at_edge.devdoc_app.get_att('Outputs.CheckAuthHandler').to_string()
        httpheaders = auth_at_edge.devdoc_app.get_att('Outputs.HttpHeadersHandler').to_string()
        if not (parse or refresh or signout or check or httpheaders):
            raise Exception('Edge functions not found !')

        cloudfront_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-{construct_id}',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
            server_access_logs_bucket=self.server_access_logs_bucket,
            server_access_logs_prefix=f'{resource_prefix}-{envname}-{construct_id}',
        )

        origin_access_identity = cloudfront.OriginAccessIdentity(
            self,
            f'{construct_id}OriginAccessIdentity',
            comment='Allows Read-Access from CloudFront',
        )

        cloudfront_bucket.grant_read(origin_access_identity)

        cloudfront_distribution = cloudfront.Distribution(
            self,
            f'{construct_id}Distribution',
            certificate=certificate,
            domain_names=domain_names,
            ssl_support_method=ssl_support_method,
            minimum_protocol_version=security_policy,
            default_behavior=cloudfront.BehaviorOptions(
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
                origin=origins.S3Origin(bucket=cloudfront_bucket, origin_access_identity=origin_access_identity),
                edge_lambdas=[
                    cloudfront.EdgeLambda(
                        event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                        function_version=self.func_version(f'{construct_id}CheckerV', check),
                    ),
                    cloudfront.EdgeLambda(
                        event_type=cloudfront.LambdaEdgeEventType.VIEWER_RESPONSE,
                        function_version=self.http_header_func.current_version,
                    ),
                ],
            ),
            additional_behaviors={
                '/parseauth': self.additional_documentation_behavior(
                    self.func_version(f'{construct_id}ParserV', parse)
                ),
                '/refreshauth': self.additional_documentation_behavior(
                    self.func_version(f'{construct_id}RefresherV', refresh)
                ),
                '/signout': self.additional_documentation_behavior(
                    self.func_version(f'{construct_id}SingouterV', signout)
                ),
            },
            default_root_object='index.html',
            error_responses=self.error_responses(),
            web_acl_id=acl.get_att('Arn').to_string(),
            log_bucket=logging_bucket,
            log_file_prefix=f'cloudfront-logs/{construct_id}',
        )

        param_path = f'/dataall/{envname}/cloudfront/docs/user'

        domain_name_ssm_param = self.store_distribution_params(
            cloudfront_bucket, construct_id, cloudfront_distribution, param_path
        )
        return cloudfront_distribution, cloudfront_bucket, domain_name_ssm_param

    def store_distribution_params(self, cloudfront_bucket, construct_id, distribution, param_path):
        ssm.StringParameter(
            self,
            f'{construct_id}DistributionId',
            parameter_name=f'{param_path}/CloudfrontDistributionId',
            string_value=distribution.distribution_id,
        )
        domain_name = ssm.StringParameter(
            self,
            f'{construct_id}DistributionDomain',
            parameter_name=f'{param_path}/CloudfrontDistributionDomainName',
            string_value=distribution.distribution_domain_name,
        )
        ssm.StringParameter(
            self,
            f'{construct_id}CloudfrontDistributionBucket',
            parameter_name=f'{param_path}/CloudfrontDistributionBucket',
            string_value=cloudfront_bucket.bucket_name,
        )
        return domain_name

    @staticmethod
    def additional_documentation_behavior(func) -> cloudfront.BehaviorOptions:
        return cloudfront.BehaviorOptions(
            origin=origins.HttpOrigin('example.org'),
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            compress=True,
            cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
            edge_lambdas=[
                cloudfront.EdgeLambda(event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST, function_version=func)
            ],
        )

    def func_version(self, name, arn):
        return _lambda.Version.from_version_arn(self, name, version_arn=arn)

    @staticmethod
    def error_responses():
        return [
            cloudfront.ErrorResponse(
                http_status=404,
                response_http_status=404,
                ttl=Duration.seconds(0),
                response_page_path='/index.html',
            ),
            cloudfront.ErrorResponse(
                http_status=403,
                response_http_status=403,
                ttl=Duration.seconds(0),
                response_page_path='/index.html',
            ),
        ]
