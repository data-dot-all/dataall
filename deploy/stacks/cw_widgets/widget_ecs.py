from aws_cdk import (
    aws_cloudwatch as cw,
)


class CDKDashboard:
    @classmethod
    def build_ecs_cluster_cpu_widget(cls, cluster_name):
        wid = cw.GraphWidget(
            title=f'{cluster_name} CPU',
            left=[
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='CPUUtilization',
                    dimensions_map={'ClusterName': cluster_name},
                ),
            ],
        )
        return wid

    @classmethod
    def build_ecs_cluster_mem_widget(cls, cluster_name):
        wid = cw.GraphWidget(
            title=f'{cluster_name} Memory',
            left=[
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='MemoryUtilization',
                    dimensions_map={'ClusterName': cluster_name},
                ),
            ],
        )
        return wid

    @classmethod
    def build_ecs_cluster_task_count_widget(cls, cluster_name):
        wid = cw.GraphWidget(
            title=f'{cluster_name} TaskCount',
            left=[
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='TaskCount',
                    dimensions_map={'ClusterName': cluster_name},
                ),
            ],
        )
        return wid

    @classmethod
    def build_ecs_task_container_insight_cpu_widget(cls, cluster_name, task_name):
        wid = cw.GraphWidget(
            title=f'{task_name} CPU',
            left=[
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='CpuReserved',
                    dimensions_map={
                        'TaskDefinitionFamily': task_name,
                        'ClusterName': cluster_name,
                    },
                ),
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='CpuUtilized',
                    dimensions_map={
                        'TaskDefinitionFamily': task_name,
                        'ClusterName': cluster_name,
                    },
                ),
            ],
        )
        return wid

    @classmethod
    def build_ecs_task_container_insight_memory_widget(cls, cluster_name, task_name):
        wid = cw.GraphWidget(
            title=f'{task_name} Memory',
            left=[
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='MemoryReserved',
                    dimensions_map={
                        'TaskDefinitionFamily': task_name,
                        'ClusterName': cluster_name,
                    },
                ),
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='MemoryUtilized',
                    dimensions_map={
                        'TaskDefinitionFamily': task_name,
                        'ClusterName': cluster_name,
                    },
                ),
            ],
        )
        return wid

    @classmethod
    def build_ecs_task_container_insight_storage_widget(cls, cluster_name, task_name):
        wid = cw.GraphWidget(
            title=f'{task_name} Storage',
            left=[
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='StorageReadBytes',
                    dimensions_map={
                        'TaskDefinitionFamily': task_name,
                        'ClusterName': cluster_name,
                    },
                ),
                cw.Metric(
                    namespace='ECS/ContainerInsights',
                    metric_name='StorageWriteBytes',
                    dimensions_map={
                        'TaskDefinitionFamily': task_name,
                        'ClusterName': cluster_name,
                    },
                ),
            ],
        )
        return wid
