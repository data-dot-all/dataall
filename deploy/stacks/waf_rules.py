from aws_cdk import aws_wafv2 as wafv2

DEFAULT_WAF_RATE_LIMIT = 1000


def get_waf_rules(envname, name, custom_waf_rules=None, ip_set_regional=None):
    waf_rules = []
    priority = 0
    if custom_waf_rules:
        if custom_waf_rules.get('allowed_geo_list'):
            waf_rules.append(
                wafv2.CfnWebACL.RuleProperty(
                    name='GeoMatch',
                    statement=wafv2.CfnWebACL.StatementProperty(
                        not_statement=wafv2.CfnWebACL.NotStatementProperty(
                            statement=wafv2.CfnWebACL.StatementProperty(
                                geo_match_statement=wafv2.CfnWebACL.GeoMatchStatementProperty(
                                    country_codes=custom_waf_rules.get('allowed_geo_list')
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
        if custom_waf_rules.get('allowed_ip_list'):
            waf_rules.append(
                wafv2.CfnWebACL.RuleProperty(
                    name='IPMatch',
                    statement=wafv2.CfnWebACL.StatementProperty(
                        not_statement=wafv2.CfnWebACL.NotStatementProperty(
                            statement=wafv2.CfnWebACL.StatementProperty(
                                ip_set_reference_statement={'arn': ip_set_regional.attr_arn}
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
    if name != 'Cognito':
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
    if name != 'Cloudfront':
        priority += 1
        waf_rules.append(
            wafv2.CfnWebACL.RuleProperty(
                name=f'{name}RateLimit',
                statement=wafv2.CfnWebACL.StatementProperty(
                    rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                        aggregate_key_type='IP',
                        limit=(custom_waf_rules or {}).get('rate_limit', DEFAULT_WAF_RATE_LIMIT),
                        evaluation_window_sec=(custom_waf_rules or {}).get('rate_limit_window'),
                    )
                ),
                action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    sampled_requests_enabled=True,
                    cloud_watch_metrics_enabled=True,
                    metric_name=f'WAF{name}RateLimit{envname}',
                ),
                priority=priority,
            )
        )
    return waf_rules
