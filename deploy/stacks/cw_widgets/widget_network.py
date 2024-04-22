from aws_cdk import (
    aws_cloudwatch as cw,
)


class CDKDashboard:
    def build_cloudFront_errorRate_widget(cls, DistributionId):
        wid = cw.GraphWidget(
            title='AWS/CloudFront',
            left=[
                cw.Metric(
                    namespace='AWS/CloudFront',
                    metric_name='4xxErrorRate',
                    dimensions={'DistributionId': DistributionId, 'Region': 'Global'},
                ),
                cw.Metric(
                    namespace='AWS/CloudFront',
                    metric_name='5xxErrorRate',
                    dimensions={'DistributionId': DistributionId, 'Region': 'Global'},
                ),
                cw.Metric(
                    namespace='AWS/CloudFront',
                    metric_name='TotalErrorRate',
                    dimensions={'DistributionId': DistributionId, 'Region': 'Global'},
                ),
            ],
        )
        return wid

    def build_cloudFront_bytes_widget(cls, DistributionId):
        wid = cw.GraphWidget(
            title='AWS/CloudFront',
            left=[
                cw.Metric(
                    namespace='AWS/CloudFront',
                    metric_name='BytesDownloaded',
                    dimensions={'DistributionId': DistributionId, 'Region': 'Global'},
                ),
                cw.Metric(
                    namespace='AWS/CloudFront',
                    metric_name='BytesUploaded',
                    dimensions={'DistributionId': DistributionId, 'Region': 'Global'},
                ),
            ],
        )
        return wid

    def build_cloudFront_requests_widget(cls, DistributionId):
        wid = cw.GraphWidget(
            title='AWS/CloudFront',
            left=[
                cw.Metric(
                    namespace='AWS/CloudFront',
                    metric_name='Requests',
                    dimensions={'DistributionId': DistributionId, 'Region': 'Global'},
                ),
            ],
        )
        return wid

    def build_clb_count_widget(cls, LoadBalancerName):
        wid = cw.GraphWidget(
            title=LoadBalancerName,
            left=[
                cw.Metric(
                    namespace='AWS/ELB',
                    metric_name='RequestCount',
                    dimensions={'LoadBalancerName': LoadBalancerName},
                ),
            ],
        )
        return wid

    def build_alb_count_widget(cls, LoadBalancerFullName):
        wid = cw.GraphWidget(
            title=LoadBalancerFullName,
            left=[
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='ActiveConnectionCount',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='ClientTLSNegotiationErrorCount',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='RequestCount',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='RejectedConnectionCount',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='HealthyHostCount',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='UnHealthyHostCount',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='RequestCountPerTarget',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
            ],
        )
        return wid

    def build_alb_byte_widget(cls, LoadBalancerFullName):
        wid = cw.GraphWidget(
            title=LoadBalancerFullName,
            left=[
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='ProcessedBytes',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
            ],
        )
        return wid

    def build_alb_code_widget(cls, LoadBalancerFullName):
        wid = cw.GraphWidget(
            title=LoadBalancerFullName,
            left=[
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='HTTPCode_ELB_3XX_Count',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='HTTPCode_ELB_4XX_Count',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
                cw.Metric(
                    namespace='AWS/ApplicationELB',
                    metric_name='HTTPCode_ELB_5XX_Count',
                    dimensions={'LoadBalancer': LoadBalancerFullName},
                ),
            ],
        )
        return wid
