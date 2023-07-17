from aws_cdk import (
    aws_cloudwatch as cw,
)


class CDKDashboard:
    def build_aurora_writer_rep_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer ReplicaLag',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='RDSToAuroraPostgreSQLReplicaLag',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_mem_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer Buffer',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='BufferCacheHitRatio',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='FreeableMemory',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_bq_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer Transactions',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='MaximumUsedTransactionIDs',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_nw_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer Network',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='NetworkReceiveThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='NetworkThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='NetworkTransmitThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_io_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer Latency',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='DiskQueueDepth',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='ReadIOPS',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='ReadLatency',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='ReadThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='WriteIOPS',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='WriteLatency',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='WriteThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='DatabaseConnections',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_disk_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer Storage',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='FreeLocalStorage',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='SwapUsage',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_queue_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer Commit',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='CommitLatency',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='CommitThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='Deadlocks',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_instance_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer EngineUptime',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='EngineUptime',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_writer_cpu_widget(cls, DBClusterIdentifier, Role='WRITER'):
        wid = cw.GraphWidget(
            title='Writer CPUUtilization',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='CPUUtilization',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    # ---------------------------------------------------------------------------

    def build_aurora_reader_rep_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader ReplicaLag',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='RDSToAuroraPostgreSQLReplicaLag',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_mem_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader Buffer',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='BufferCacheHitRatio',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='FreeableMemory',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_bq_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader Transactions',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='MaximumUsedTransactionIDs',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_nw_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader Network',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='NetworkReceiveThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='NetworkThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='NetworkTransmitThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_io_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader Latency',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='DiskQueueDepth',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='ReadIOPS',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='ReadLatency',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='ReadThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='WriteIOPS',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='WriteLatency',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='WriteThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='DatabaseConnections',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_disk_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader Storage',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='FreeLocalStorage',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='SwapUsage',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_queue_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader EngineUptime',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='CommitLatency',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='CommitThroughput',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='Deadlocks',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_instance_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader EngineUptime',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='EngineUptime',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    def build_aurora_reader_cpu_widget(cls, DBClusterIdentifier, Role='READER'):
        wid = cw.GraphWidget(
            title='Reader CPUUtilization',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='CPUUtilization',
                    dimensions_map={
                        'DBClusterIdentifier': DBClusterIdentifier,
                        'Role': Role,
                    },
                ),
            ],
        )
        return wid

    # ---------------------------------------------------------------------------

    def build_aurora_rep_widget(cls, DBClusterIdentifier):
        wid = cw.GraphWidget(
            title='ReplicaLag',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='AuroraReplicaLag',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='AuroraReplicaLagMaximum',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='AuroraReplicaLagMinimum',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
            ],
        )
        return wid

    def build_aurora_bk_widget(cls, DBClusterIdentifier):
        wid = cw.GraphWidget(
            title='Retention',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='BackupRetentionPeriodStorageUsed',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='SnapshotStorageUsed',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
            ],
        )
        return wid

    def build_aurora_disk_widget(cls, DBClusterIdentifier):
        wid = cw.GraphWidget(
            title='DiskUsage',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='TransactionLogsDiskUsage',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='VolumeBytesUsed',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
            ],
        )
        return wid

    def build_aurora_io_widget(cls, DBClusterIdentifier):
        wid = cw.GraphWidget(
            title='VolumeWriteIOPs',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='VolumeWriteIOPs',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
            ],
        )
        return wid

    def build_aurora_bill_widget(cls, DBClusterIdentifier):
        wid = cw.GraphWidget(
            title='Backup',
            left=[
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='TotalBackupStorageBilled',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
                cw.Metric(
                    namespace='AWS/RDS',
                    metric_name='VolumeReadIOPs',
                    dimensions_map={'DBClusterIdentifier': DBClusterIdentifier},
                ),
            ],
        )
        return wid
