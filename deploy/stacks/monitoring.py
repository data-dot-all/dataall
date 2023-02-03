from aws_cdk import (
    aws_cloudwatch as cw,
    aws_ecs as ecs,
    aws_lambda as _lambda,
    aws_kms as kms,
    aws_ssm as ssm,
    aws_cloudwatch_actions as cwa,
    aws_sns as sns,
    aws_logs as logs,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    Fn,
)

from .pyNestedStack import pyNestedClass
from .cw_widgets import widget_rds, widget_api, widget_ecs


class MonitoringStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        lambdas: [_lambda.Function] = None,
        database='dataalldevdb',
        ecs_cluster: ecs.Cluster = None,
        ecs_task_definitions: [ecs.FargateTaskDefinition] = None,
        backend_api=None,
        opensearch_domain: str = None,
        opensearch_serverless_collection_id: str = None,
        opensearch_serverless_collection_name: str = None,
        queue_name: str = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.alarms_topic, self.cw_alarm_action = self.create_alarms_topic(
            envname, resource_prefix
        )

        self.create_cw_alarms(
            backend_api,
            lambdas,
            database,
            opensearch_domain,
            opensearch_serverless_collection_id,
            opensearch_serverless_collection_name,
            queue_name,
            envname,
            resource_prefix,
        )

        self.create_cw_dashboard(
            backend_api,
            database,
            ecs_cluster,
            ecs_task_definitions,
            envname,
            lambdas,
            resource_prefix,
        )

    def create_alarms_topic(self, envname, resource_prefix):
        key = kms.Key(
            self,
            f'{resource_prefix}-{envname}-alarms-topic-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{resource_prefix}-{envname}-alarms-topic-key',
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.AccountPrincipal(account_id=self.account),
                        ],
                        actions=['kms:*'],
                    ),
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.ServicePrincipal(service='cloudwatch.amazonaws.com'),
                        ],
                        actions=['kms:GenerateDataKey*', 'kms:Decrypt'],
                    ),
                ],
            ),
        )
        alarms_topic = sns.Topic(
            self,
            f'AlarmsTopic',
            topic_name=f'{resource_prefix}-{envname}-alarms-topic',
            master_key=key,
        )
        cw_alarm_action = cwa.SnsAction(alarms_topic)
        ssm.StringParameter(
            self,
            'AlarmTopicParam',
            parameter_name=f'/dataall/{envname}/sns/alarmsTopic',
            string_value=alarms_topic.topic_arn,
        )
        return alarms_topic, cw_alarm_action

    def create_cw_alarms(
        self,
        backend_api,
        lambdas,
        database,
        openseach_domain,
        opensearch_serverless_collection_id,
        opensearch_serverless_collection_name,
        queue_name,
        envname,
        resource_prefix,
    ):
        lambda_function: _lambda.Function
        for index, lambda_function in enumerate(lambdas):
            self.set_function_alarms(
                f'Alarm{index}',
                lambda_function,
                self.cw_alarm_action,
                resource_prefix,
            )
        self.set_waf_alarms(
            f'{resource_prefix}-{envname}-WafApiGatewayRateLimitBreached',
            Fn.import_value(f'{resource_prefix}-{envname}-api-webacl'),
            self.cw_alarm_action,
        )
        self.set_api_alarms(
            f'{resource_prefix}-{envname}-api-alarm', backend_api, self.cw_alarm_action
        )
        self.set_aurora_alarms(
            f'{resource_prefix}-{envname}-aurora-alarm', database, self.cw_alarm_action
        )
        if openseach_domain:
            self.set_es_alarms(
                f'{resource_prefix}-{envname}-opensearch-alarm',
                openseach_domain,
                self.cw_alarm_action,
            )
        if opensearch_serverless_collection_id:
            self.set_aoss_alarms(
                f'{resource_prefix}-{envname}-opensearch-serverless-alarm',
                opensearch_serverless_collection_id,
                opensearch_serverless_collection_name,
                self.cw_alarm_action,
            )
        self.set_sqs_alarms(
            f'{resource_prefix}-{envname}-sqs-alarm',
            queue_name,
            self.cw_alarm_action,
        )

    def create_cw_dashboard(
        self,
        backend_api,
        database,
        ecs_cluster,
        ecs_task_definitions,
        envname,
        lambdas,
        resource_prefix,
    ):
        cf_rds = widget_rds.CDKDashboard()
        cf_ecs = widget_ecs.CDKDashboard()
        cf_api = widget_api.CDKDashboard()
        dashboard = cw.Dashboard(
            self,
            id='CWDashboard',
            dashboard_name=f'{resource_prefix}-{envname}-dashboard',
        )
        dashboard.add_widgets(cw.TextWidget(width=24, markdown='# API Gateway'))
        api_nickname = backend_api
        api_name = backend_api
        dashboard.add_widgets(
            cf_api.build_apig_duration(api_name, api_nickname),
            cf_api.build_apig_errors(api_name, api_nickname),
        )
        dashboard.add_widgets(cw.TextWidget(width=24, markdown='# Lambda Functions'))
        l: _lambda.Function
        for l in lambdas:
            dashboard.add_widgets(
                cf_api.build_lambda_hard_errors(l.function_name, l.function_name),
                cf_api.build_lambda_invocations(l.function_name, l.function_name),
                cf_api.build_lambda_duration(l.function_name, l.function_name),
            )
        if ecs_cluster:
            dashboard.add_widgets(cw.TextWidget(width=24, markdown='# ECS Cluster'))
            cluster_name = ecs_cluster.cluster_name
            dashboard.add_widgets(
                cf_ecs.build_ecs_cluster_cpu_widget(cluster_name),
                cf_ecs.build_ecs_cluster_mem_widget(cluster_name),
                cf_ecs.build_ecs_cluster_task_count_widget(cluster_name),
            )

            if ecs_task_definitions:
                dashboard.add_widgets(cw.TextWidget(width=24, markdown='# ECS Tasks'))
                task: ecs.FargateTaskDefinition
                for task in ecs_task_definitions:
                    dashboard.add_widgets(
                        cf_ecs.build_ecs_task_container_insight_cpu_widget(
                            cluster_name, task.family
                        ),
                        cf_ecs.build_ecs_task_container_insight_memory_widget(
                            cluster_name, task.family
                        ),
                        cf_ecs.build_ecs_task_container_insight_storage_widget(
                            cluster_name, task.family
                        ),
                    )
        if database:
            dashboard.add_widgets(
                cw.TextWidget(width=24, markdown='# Aurora Serverless Database')
            )
            DBClusterIdentifier = database
            dashboard.add_widgets(
                cf_rds.build_aurora_writer_rep_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_mem_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_bq_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_nw_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_io_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_disk_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_queue_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_instance_widget(DBClusterIdentifier),
                cf_rds.build_aurora_writer_cpu_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_rep_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_mem_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_bq_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_nw_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_io_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_disk_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_queue_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_instance_widget(DBClusterIdentifier),
                cf_rds.build_aurora_reader_cpu_widget(DBClusterIdentifier),
                cf_rds.build_aurora_rep_widget(DBClusterIdentifier),
                cf_rds.build_aurora_bk_widget(DBClusterIdentifier),
                cf_rds.build_aurora_disk_widget(DBClusterIdentifier),
                cf_rds.build_aurora_io_widget(DBClusterIdentifier),
                cf_rds.build_aurora_bill_widget(DBClusterIdentifier),
            )

    def set_function_alarms(
        self, alarm_name, lambda_function, cw_alarm_action, resource_prefix
    ):
        error_metric = cw.Metric(
            namespace=resource_prefix,
            metric_name=f'{lambda_function.function_name}-error-metric',
            label='Function ERROR metric',
            statistic='Sum',
            period=Duration.seconds(10),
        )
        logs.MetricFilter(
            self,
            f'{alarm_name}-error-metric-filter',
            log_group=lambda_function.log_group,
            metric_name=error_metric.metric_name,
            metric_value='1',
            metric_namespace=error_metric.namespace,
            filter_pattern=logs.FilterPattern.literal('ERROR'),
        )
        error_metric_alarm = cw.Alarm(
            self,
            f'{alarm_name}-error-metric-alarm',
            metric=error_metric,
            evaluation_periods=1,
            threshold=1,
            alarm_name=f'{lambda_function.function_name}-error-metric-alarm',
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        error_metric_alarm.add_alarm_action(cw_alarm_action)
        error_metric_alarm.add_ok_action(cw_alarm_action)

        lambda_error = cw.Alarm(
            self,
            f'{alarm_name}-invocation-errors',
            metric=lambda_function.metric_errors(),
            evaluation_periods=1,
            threshold=1,
            alarm_name=f'{lambda_function.function_name}-invocation-errors',
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        lambda_error.add_alarm_action(cw_alarm_action)
        lambda_error.add_ok_action(cw_alarm_action)
        lambda_throttles = cw.Alarm(
            self,
            f'{alarm_name}-throttles',
            metric=lambda_function.metric_throttles(),
            evaluation_periods=1,
            threshold=1,
            alarm_name=f'{lambda_function.function_name}-throttles',
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        lambda_throttles.add_alarm_action(cw_alarm_action)
        lambda_throttles.add_ok_action(cw_alarm_action)

    def set_api_alarms(self, alarm_name, api_name, cw_alarm_action):
        api_count = cw.Metric(
            namespace='AWS/ApiGateway',
            metric_name='Count',
            dimensions_map={'ApiName': api_name},
        )
        self._set_alarm(
            f'{alarm_name}-max-calls', api_count, cw_alarm_action, threshold=100
        )
        api_5xx_errors = cw.Metric(
            namespace='AWS/ApiGateway',
            metric_name='5XXError',
            dimensions_map={'ApiName': api_name},
        )
        self._set_alarm(
            f'{alarm_name}-5XXErrors', api_5xx_errors, cw_alarm_action, threshold=1
        )
        api_4xx_errors = cw.Metric(
            namespace='AWS/ApiGateway',
            metric_name='4XXError',
            dimensions_map={'ApiName': api_name},
        )
        self._set_alarm(
            f'{alarm_name}-4XXErrors', api_4xx_errors, cw_alarm_action, threshold=1
        )

    def set_aurora_alarms(self, alarm_name, db_identifier, cw_alarm_action):
        cpu_alarm = cw.Metric(
            namespace='AWS/RDS',
            metric_name='CPUUtilization',
            dimensions_map={'DBInstanceIdentifier': db_identifier},
            statistic='Sum',
            period=Duration.minutes(1),
        )
        self._set_alarm(
            f'{alarm_name}-CPUUtilization80', cpu_alarm, cw_alarm_action, threshold=80
        )
        self._set_alarm(
            f'{alarm_name}-CPUUtilization90', cpu_alarm, cw_alarm_action, threshold=90
        )

    def _set_alarm(self, alarm_name, api_count, cw_alarm_action, threshold=1):
        api_error = cw.Alarm(
            self,
            alarm_name,
            metric=api_count,
            evaluation_periods=1,
            threshold=threshold,
            alarm_name=alarm_name,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        api_error.add_alarm_action(cw_alarm_action)
        api_error.add_ok_action(cw_alarm_action)

    def set_waf_alarms(self, alarm_name, web_acl_id, cw_alarm_action):
        waf_metric = cw.Metric(
            metric_name='BlockedRequests',
            namespace='AWS/WAFV2',
            statistic='Sum',
            dimensions_map=dict(
                rule='waf-apigateway-ratelimit',
                WebACL=web_acl_id,
                Region=self.region,
            ),
            period=Duration.minutes(1),
        )
        waf_alarm = cw.Alarm(
            self,
            alarm_name,
            metric=waf_metric,
            evaluation_periods=1,
            threshold=1000,
            alarm_name=alarm_name,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        waf_alarm.add_alarm_action(cw_alarm_action)
        waf_alarm.add_ok_action(cw_alarm_action)

    def set_es_alarms(self, alarm_name, domain_name, cw_alarm_action):
        self._set_es_alarm(
            domain_name,
            f'{alarm_name}-cluster-red',
            'ClusterStatus.red',
            1,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            1,
            1,
            'max',
            cw_alarm_action,
        )
        self._set_es_alarm(
            domain_name,
            f'{alarm_name}-cluster-yellow',
            'ClusterStatus.yellow',
            1,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            1,
            1,
            'max',
            cw_alarm_action,
        )
        self._set_es_alarm(
            domain_name,
            f'{alarm_name}-cluster-IndexWritesBlocked',
            'ClusterIndexWritesBlocked',
            1,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            5,
            1,
            'max',
            cw_alarm_action,
        )
        self._set_es_alarm(
            domain_name,
            f'{alarm_name}-cluster-CPUUtilization',
            'CPUUtilization',
            80,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            15,
            3,
            'avg',
            cw_alarm_action,
        )
        self._set_es_alarm(
            domain_name,
            f'{alarm_name}-cluster-JVMMemoryPressure',
            'JVMMemoryPressure',
            80,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            5,
            3,
            'max',
            cw_alarm_action,
        )

    def set_aoss_alarms(self, alarm_name, collection_id, collection_name, cw_alarm_action):
        self._set_aoss_alarm(
            collection_id,
            collection_name,
            f'{alarm_name}-collection-ActiveCollection',
            'ActiveCollection',
            1,
            cw.ComparisonOperator.LESS_THAN_THRESHOLD,
            1,
            1,
            'max',
            cw_alarm_action,
            cw.TreatMissingData.BREACHING,
        )
        self._set_aoss_alarm(
            collection_id,
            collection_name,
            f'{alarm_name}-collection-IngestionRequestErrors',
            'IngestionRequestErrors',
            1,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            5,
            1,
            'max',
            cw_alarm_action,
        )
        self._set_aoss_alarm(
            collection_id,
            collection_name,
            f'{alarm_name}-collection-SearchRequestErrors',
            'SearchRequestErrors',
            1,
            cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            5,
            1,
            'max',
            cw_alarm_action,
        )

    def _set_es_alarm(
        self,
        domain_name,
        alarm_name,
        metric_name,
        threshold,
        comparison_operator,
        period,
        evaluation_periods,
        statistic,
        cw_alarm_action,
    ) -> None:
        cw_alarm = cw.Alarm(
            self,
            alarm_name,
            alarm_name=alarm_name,
            metric=cw.Metric(
                metric_name=metric_name,
                namespace='AWS/ES',
                dimensions_map={'DomainName': domain_name, 'ClientId': self.account},
                period=Duration.minutes(period),
                statistic=statistic,
            ),
            threshold=threshold,
            comparison_operator=comparison_operator,
            evaluation_periods=evaluation_periods,
            treat_missing_data=cw.TreatMissingData.MISSING,
        )
        cw_alarm.add_alarm_action(cw_alarm_action)
        cw_alarm.add_ok_action(cw_alarm_action)

    def _set_aoss_alarm(
        self,
        collection_id,
        collection_name,
        alarm_name,
        metric_name,
        threshold,
        comparison_operator,
        period,
        evaluation_periods,
        statistic,
        cw_alarm_action,
        treat_missing_data=cw.TreatMissingData.MISSING,
    ) -> None:
        cw_alarm = cw.Alarm(
            self,
            alarm_name,
            alarm_name=alarm_name,
            metric=cw.Metric(
                metric_name=metric_name,
                namespace='AWS/AOSS',
                dimensions_map={
                    'CollectionId': collection_id,
                    'CollectionName': collection_name,
                    'ClientId': self.account,
                },
                period=Duration.minutes(period),
                statistic=statistic,
            ),
            threshold=threshold,
            comparison_operator=comparison_operator,
            evaluation_periods=evaluation_periods,
            treat_missing_data=treat_missing_data,
        )
        cw_alarm.add_alarm_action(cw_alarm_action)
        cw_alarm.add_ok_action(cw_alarm_action)

    def set_sqs_alarms(self, alarm_name, queue_name, cw_alarm_action):
        max_messages = cw.Metric(
            namespace='AWS/SQS',
            metric_name='NumberOfMessagesSent',
            dimensions_map={'MyQueue': queue_name},
            statistic='Sum',
            period=Duration.minutes(5),
        )
        queue_nb_msg_alarm = cw.Alarm(
            self,
            f'{alarm_name}-NumberOfMessagesSent',
            metric=max_messages,
            evaluation_periods=1,
            threshold=10000,
            alarm_name=f'{alarm_name}-NumberOfMessagesSent',
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        queue_nb_msg_alarm.add_alarm_action(cw_alarm_action)
        queue_nb_msg_alarm.add_ok_action(cw_alarm_action)
