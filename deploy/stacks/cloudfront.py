import hashlib
import os

from aws_cdk import (
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
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
)

from .pyNestedStack import pyNestedClass
from .solution_bundling import SolutionBundling

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
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        # Create IP set if IP filtering enabled
        ip_set_cloudfront=None
        if custom_waf_rules and custom_waf_rules.get("allowed_ip_list"):
            ip_set_cloudfront = wafv2.CfnIPSet(
                self,
                "DataallCloudfrontIPSet",
                name=f"{resource_prefix}-{envname}-ipset-cloudfront",
                description=f"IP addresses to allow for Dataall {envname}",
                addresses=custom_waf_rules.get("allowed_ip_list"),
                ip_address_version="IPV4",
                scope="CLOUDFRONT"
            )

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
                                        "arn" : ip_set_cloudfront.attr_arn
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
            rules=waf_rules,
        )

        logging_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-logging',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
        )

        frontend_alternate_domain = None
        userguide_alternate_domain = None
        frontend_alias_configuration = None
        userguide_alias_configuration = None

        cloudfront_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-frontend',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
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

            certificate = acm.Certificate(
                self,
                'CustomDomainCertificate',
                domain_name=custom_domain_name,
                subject_alternative_names=[f'*.{custom_domain_name}'],
                validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
            )

            frontend_alias_configuration = (
                cloudfront.ViewerCertificate.from_acm_certificate(
                    aliases=[frontend_alternate_domain],
                    certificate=certificate,
                    ssl_method=cloudfront.SSLMethod.SNI,
                    security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
                )
            )

        cloudfront_distribution = cloudfront.CloudFrontWebDistribution(
            self,
            'CloudFrontDistribution',
            viewer_certificate=frontend_alias_configuration,
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=cloudfront_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True, default_ttl=Duration.hours(1)
                        )
                    ],
                )
            ],
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            default_root_object='index.html',
            error_configurations=[
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=404,
                    response_code=404,
                    error_caching_min_ttl=0,
                    response_page_path='/index.html',
                ),
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=403,
                    response_code=403,
                    error_caching_min_ttl=0,
                    response_page_path='/index.html',
                ),
            ],
            web_acl_id=acl.get_att('Arn').to_string(),
            logging_config=cloudfront.LoggingConfiguration(
                bucket=logging_bucket, prefix='cloudfront-logs/frontend'
            ),
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

        # Lambda@edge for http_header_redirection
        docs_http_headers = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                'custom_resources',
                'docs_http_headers',
            )
        )
        (
            self.http_header_func,
            self.http_header_func_version,
        ) = self.build_docs_http_headers(docs_http_headers, envname, resource_prefix)

        
        if userguide_alternate_domain:
            userguide_alias_configuration = (
                cloudfront.ViewerCertificate.from_acm_certificate(
                    aliases=[userguide_alternate_domain],
                    certificate=certificate,
                    ssl_method=cloudfront.SSLMethod.SNI,
                    security_policy=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
                )
            )

        userguide_docs_distribution, user_docs_bucket = self.build_static_site(
            f'userguide',
            acl,
            auth_at_edge,
            envname,
            resource_prefix,
            userguide_alias_configuration,
            logging_bucket,
        )
        if frontend_alternate_domain:
            frontend_record = route53.ARecord(
                self,
                'CloudFrontFrontendDomain',
                record_name=frontend_alternate_domain,
                zone=hosted_zone,
                target=route53.RecordTarget.from_alias(
                    route53_targets.CloudFrontTarget(cloudfront_distribution)
                ),
            )
        if userguide_alternate_domain:
            userguide_record = route53.ARecord(
                self,
                'CloudFrontUserguideDomain',
                record_name=userguide_alternate_domain,
                zone=hosted_zone,
                target=route53.RecordTarget.from_alias(
                    route53_targets.CloudFrontTarget(userguide_docs_distribution)
                ),
            )

        if tooling_account_id:
            cross_account_deployment_role = iam.Role(
                self,
                f'S3DeploymentRole{envname}',
                role_name=f'{resource_prefix}-{envname}-S3DeploymentRole',
                assumed_by=iam.AccountPrincipal(tooling_account_id),
            )
            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        's3:Get*',
                        's3:Put*',
                    ],
                    resources=[
                        f'{cloudfront_bucket.bucket_arn}/*',
                        f'{user_docs_bucket.bucket_arn}/*',
                    ],
                )
            )
            cross_account_deployment_role.add_to_policy(
                iam.PolicyStatement(
                    actions=['cloudfront:CreateInvalidation', 's3:List*'],
                    resources=['*'],
                )
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
                    resources=[
                        f'arn:aws:rum:*:{self.account}:appmonitor/*{resource_prefix}*'
                    ],
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
        self.user_docs_bucket = user_docs_bucket
        self.user_docs_distribution = userguide_docs_distribution
        self.cross_account_deployment_role = (
            cross_account_deployment_role.role_name
            if cross_account_deployment_role
            else None
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
            runtime=_lambda.Runtime.NODEJS_14_X,
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
        alias_configuration,
        logging_bucket,
    ):

        parse = auth_at_edge.devdoc_app.get_att('Outputs.ParseAuthHandler').to_string()
        refresh = auth_at_edge.devdoc_app.get_att(
            'Outputs.RefreshAuthHandler'
        ).to_string()
        signout = auth_at_edge.devdoc_app.get_att('Outputs.SignOutHandler').to_string()
        check = auth_at_edge.devdoc_app.get_att('Outputs.CheckAuthHandler').to_string()
        httpheaders = auth_at_edge.devdoc_app.get_att(
            'Outputs.HttpHeadersHandler'
        ).to_string()

        if not (parse or refresh or signout or check or httpheaders):
            raise Exception('Edge functions not found !')

        cloudfront_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-{construct_id}',
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        origin_access_identity = cloudfront.OriginAccessIdentity(
            self,
            f'{construct_id}OriginAccessIdentity',
            comment='Allows Read-Access from CloudFront',
        )

        cloudfront_bucket.grant_read(origin_access_identity)

        cloudfront_distribution = cloudfront.CloudFrontWebDistribution(
            self,
            f'{construct_id}Distribution',
            viewer_certificate=alias_configuration,
            origin_configs=[
                cloudfront.SourceConfiguration(
                    custom_origin_source=cloudfront.CustomOriginConfig(
                        domain_name='example.org',
                        origin_protocol_policy=cloudfront.OriginProtocolPolicy.MATCH_VIEWER,
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            path_pattern='/parseauth',
                            compress=True,
                            forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                                query_string=True
                            ),
                            lambda_function_associations=[
                                cloudfront.LambdaFunctionAssociation(
                                    event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                                    lambda_function=_lambda.Version.from_version_arn(
                                        self,
                                        f'{construct_id}ParserV',
                                        version_arn=parse,
                                    ),
                                )
                            ],
                        ),
                        cloudfront.Behavior(
                            path_pattern='/refreshauth',
                            compress=True,
                            forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                                query_string=True
                            ),
                            lambda_function_associations=[
                                cloudfront.LambdaFunctionAssociation(
                                    event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                                    lambda_function=_lambda.Version.from_version_arn(
                                        self,
                                        f'{construct_id}RefresherV',
                                        version_arn=refresh,
                                    ),
                                )
                            ],
                        ),
                        cloudfront.Behavior(
                            path_pattern='/signout',
                            compress=True,
                            forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                                query_string=True
                            ),
                            lambda_function_associations=[
                                cloudfront.LambdaFunctionAssociation(
                                    event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                                    lambda_function=_lambda.Version.from_version_arn(
                                        self,
                                        f'{construct_id}SingouterV',
                                        version_arn=signout,
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=cloudfront_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                            compress=True,
                            forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                                query_string=True
                            ),
                            lambda_function_associations=[
                                cloudfront.LambdaFunctionAssociation(
                                    event_type=cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                                    lambda_function=_lambda.Version.from_version_arn(
                                        self,
                                        f'{construct_id}CheckerV',
                                        version_arn=check,
                                    ),
                                ),
                                cloudfront.LambdaFunctionAssociation(
                                    event_type=cloudfront.LambdaEdgeEventType.ORIGIN_RESPONSE,
                                    lambda_function=self.http_header_func.current_version,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            default_root_object='index.html',
            error_configurations=[
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=404,
                    response_code=404,
                    error_caching_min_ttl=0,
                    response_page_path='/index.html',
                ),
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=403,
                    response_code=403,
                    error_caching_min_ttl=0,
                    response_page_path='/index.html',
                ),
            ],
            web_acl_id=acl.get_att('Arn').to_string(),
            logging_config=cloudfront.LoggingConfiguration(
                bucket=logging_bucket, prefix=f'cloudfront-logs/{construct_id}'
            ),
        )

        param_path = f'/dataall/{envname}/cloudfront/docs/user'

        self.store_distribution_params(
            cloudfront_bucket, construct_id, cloudfront_distribution, param_path
        )
        return cloudfront_distribution, cloudfront_bucket

    def store_distribution_params(
        self, cloudfront_bucket, construct_id, distribution, param_path
    ):
        ssm.StringParameter(
            self,
            f'{construct_id}DistributionId',
            parameter_name=f'{param_path}/CloudfrontDistributionId',
            string_value=distribution.distribution_id,
        )
        ssm.StringParameter(
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
