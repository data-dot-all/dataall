from aws_cdk import (
    aws_cloudwatch as cw,
)


class CDKDashboard:
    def build_lambda_hard_errors(cls, function_name, function_nickname):
        wid = cw.GraphWidget(
            title=f'{function_nickname} - Lambda Hard Errors',
            left=[
                cw.Metric(
                    label=f'{function_nickname} - Errors',
                    namespace='AWS/Lambda',
                    metric_name='Errors',
                    dimensions_map={'FunctionName': function_name},
                    statistic='Sum',
                )
            ],
        )
        return wid

    def build_lambda_invocations(cls, function_name, function_nickname):
        wid = cw.GraphWidget(
            title=f'{function_nickname} - Invocations and Executions',
            left=[
                cw.Metric(
                    label=f'{function_nickname} - Invocations',
                    namespace='AWS/Lambda',
                    metric_name='Invocations',
                    dimensions_map={'FunctionName': function_name},
                    statistic='Sum',
                ),
                cw.Metric(
                    label=f'{function_nickname} - ConcurrentExecutions',
                    namespace='AWS/Lambda',
                    metric_name='ConcurrentExecutions',
                    dimensions_map={'FunctionName': function_name},
                    statistic='Maximum',
                ),
            ],
        )
        return wid

    def build_lambda_duration(cls, function_name, function_nickname):
        wid = cw.GraphWidget(
            title=f'{function_nickname} - Duration',
            left=[
                cw.Metric(
                    label=f'{function_nickname} - p95',
                    namespace='AWS/Lambda',
                    metric_name='Duration',
                    dimensions_map={'FunctionName': function_name},
                    statistic='p95',
                ),
                cw.Metric(
                    label=f'{function_nickname} - avg',
                    namespace='AWS/Lambda',
                    metric_name='Duration',
                    dimensions_map={'FunctionName': function_name},
                    statistic='Average',
                ),
                cw.Metric(
                    label=f'{function_nickname} - max',
                    namespace='AWS/Lambda',
                    metric_name='Duration',
                    dimensions_map={'FunctionName': function_name},
                    statistic='Maximum',
                ),
            ],
        )
        return wid

    def build_apig_duration(cls, api_name, api_nickname):
        wid = cw.GraphWidget(
            title=f'{api_nickname} - Duration',
            left=[
                cw.Metric(
                    label=f'{api_nickname} - p95',
                    namespace='AWS/ApiGateway',
                    metric_name='Duration',
                    dimensions_map={'ApiName': api_name},
                    statistic='p95',
                ),
                cw.Metric(
                    label=f'{api_nickname} - avg',
                    namespace='AWS/ApiGateway',
                    metric_name='Duration',
                    dimensions_map={'ApiName': api_name},
                    statistic='Average',
                ),
                cw.Metric(
                    label=f'{api_nickname} - max',
                    namespace='AWS/ApiGateway',
                    metric_name='Duration',
                    dimensions_map={'ApiName': api_name},
                    statistic='Maximum',
                ),
            ],
        )
        return wid

    def build_apig_errors(cls, api_name, api_nickname):
        wid = cw.GraphWidget(
            title=f'{api_nickname} - HTTP Errors',
            left=[
                cw.Metric(
                    label=f'{api_nickname} - 5XXError',
                    namespace='AWS/ApiGateway',
                    metric_name='5XXError',
                    dimensions_map={'ApiName': api_name},
                    statistic='Sum',
                ),
                cw.Metric(
                    label=f'{api_nickname} - 4XXError',
                    namespace='AWS/ApiGateway',
                    metric_name='4XXError',
                    dimensions_map={'ApiName': api_name},
                    statistic='Sum',
                ),
            ],
        )
        return wid
