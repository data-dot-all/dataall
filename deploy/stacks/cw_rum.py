from aws_cdk import (
    aws_cloudwatch as cw,
    aws_rum as rum,
    aws_ssm as ssm,
    aws_iam as iam,
    CfnTag,
    Duration,
)

from .pyNestedStack import pyNestedClass


class CloudWatchRumStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        cw_alarm_action=None,
        cognito_identity_pool_id: str = None,
        cognito_identity_pool_role_arn: str = None,
        custom_domain_name: str = None,
        tooling_account_id: str = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.create_rum_app_monitor(
            cognito_identity_pool_id,
            cognito_identity_pool_role_arn,
            custom_domain_name,
            envname,
            resource_prefix,
            tooling_account_id,
            cw_alarm_action,
        )

    def create_rum_app_monitor(
        self,
        cognito_identity_pool_id,
        cognito_identity_pool_role_arn,
        custom_domain_name,
        envname,
        resource_prefix,
        tooling_account_id,
        cw_alarm_action,
    ):
        monitor_name = f'{resource_prefix}-{envname}-monitor'
        rum.CfnAppMonitor(
            self,
            f'{resource_prefix}RumAppMonitor',
            domain=custom_domain_name or f'{resource_prefix}.{envname}.change.me',
            name=monitor_name,
            cw_log_enabled=True,
            app_monitor_configuration=rum.CfnAppMonitor.AppMonitorConfigurationProperty(
                allow_cookies=True,
                enable_x_ray=True,
                session_sample_rate=1,
                telemetries=['errors', 'performance', 'http'],
                identity_pool_id=cognito_identity_pool_id,
                guest_role_arn=cognito_identity_pool_role_arn,
            ),
            tags=[CfnTag(key='Application', value='dataall')],
        )
        self.set_rum_alarms(
            f'{resource_prefix}-{envname}-rum-jserrors-alarm',
            monitor_name,
            cw_alarm_action,
        )
        cross_account_rum_config_role = iam.Role(
            self,
            f'{resource_prefix}-{envname}-rum-config-role',
            role_name=f'{resource_prefix}-{envname}-rum-config-role',
            assumed_by=iam.AccountPrincipal(tooling_account_id),
        )
        cross_account_rum_config_role.add_to_policy(
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
        cross_account_rum_config_role.add_to_policy(
            iam.PolicyStatement(
                actions=['rum:GetAppMonitor', 'rum:UpdateAppMonitor'],
                resources=[f'arn:aws:rum:{self.region}:{self.account}:appmonitor/{monitor_name}'],
            ),
        )
        ssm.StringParameter(
            self,
            'RumConfigRoleName',
            parameter_name=f'/dataall/{envname}/rum/crossAccountRole',
            string_value=cross_account_rum_config_role.role_name,
        )

    def set_rum_alarms(self, alarm_name, app_monitor, cw_alarm_action):
        js_errors_metric = cw.Metric(
            namespace='AWS/RUM',
            metric_name='JsErrorCount',
            dimensions_map={'application_name': app_monitor},
            statistic='Sum',
            period=Duration.minutes(1),
        )
        rum_js_errors_alarm = cw.Alarm(
            self,
            alarm_name,
            metric=js_errors_metric,
            evaluation_periods=1,
            threshold=1,
            alarm_name=alarm_name,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        rum_js_errors_alarm.add_alarm_action(cw_alarm_action)
        rum_js_errors_alarm.add_ok_action(cw_alarm_action)
