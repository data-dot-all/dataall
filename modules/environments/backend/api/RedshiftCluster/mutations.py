from backend.api import gql
from .resolvers import *

createRedshiftCluster = gql.MutationField(
    name='createRedshiftCluster',
    args=[
        gql.Argument(name='environmentUri', type=gql.String),
        gql.Argument(name='clusterInput', type=gql.Ref('NewClusterInput')),
    ],
    type=gql.Ref('RedshiftCluster'),
    resolver=create,
)

deleteRedshiftCluster = gql.MutationField(
    name='deleteRedshiftCluster',
    args=[
        gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    type=gql.Boolean,
    resolver=delete,
)

rebootRedshiftCluster = gql.MutationField(
    name='rebootRedshiftCluster',
    args=[gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=reboot_cluster,
)

resumeRedshiftCluster = gql.MutationField(
    name='resumeRedshiftCluster',
    args=[gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=resume_cluster,
)

pauseRedshiftCluster = gql.MutationField(
    name='pauseRedshiftCluster',
    args=[gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=pause_cluster,
)

importRedshiftCluster = gql.MutationField(
    name='importRedshiftCluster',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(
            name='clusterInput', type=gql.NonNullableType(gql.Ref('ImportClusterInput'))
        ),
    ],
    type=gql.Ref('RedshiftCluster'),
    resolver=import_cluster,
)

addDatasetToRedshiftCluster = gql.MutationField(
    name='addDatasetToRedshiftCluster',
    args=[
        gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=add_dataset_to_cluster,
)


removeDatasetFromRedshiftCluster = gql.MutationField(
    name='removeDatasetFromRedshiftCluster',
    args=[
        gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=remove_dataset_from_cluster,
)

enableRedshiftClusterDatasetTableCopy = gql.MutationField(
    name='enableRedshiftClusterDatasetTableCopy',
    args=[
        gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='schema', type=gql.String),
        gql.Argument(name='dataLocation', type=gql.String),
    ],
    type=gql.Boolean,
    resolver=enable_dataset_table_copy,
)

disableRedshiftClusterDatasetTableCopy = gql.MutationField(
    name='disableRedshiftClusterDatasetTableCopy',
    args=[
        gql.Argument(name='clusterUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=disable_dataset_table_copy,
)
