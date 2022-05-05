from ... import gql
from .resolvers import *

getRedshiftCluster = gql.QueryField(
    name="getRedshiftCluster",
    args=[gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("RedshiftCluster"),
    resolver=get_cluster,
)


getRedshiftClusterConsoleAccess = gql.QueryField(
    name="getRedshiftClusterConsoleAccess",
    args=[gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_console_access,
)

listRedshiftClusterAvailableDatasets = gql.QueryField(
    name="listRedshiftClusterAvailableDatasets",
    args=[
        gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="filter", type=gql.Ref("RedshiftClusterDatasetFilter")),
    ],
    resolver=list_cluster_available_datasets,
    type=gql.Ref("DatasetSearchResult"),
)

listRedshiftClusterDatasets = gql.QueryField(
    name="listRedshiftClusterDatasets",
    args=[
        gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="filter", type=gql.Ref("RedshiftClusterDatasetFilter")),
    ],
    resolver=list_cluster_datasets,
    type=gql.Ref("DatasetSearchResult"),
)

listRedshiftClusterAvailableDatasetTables = gql.QueryField(
    name="listRedshiftClusterAvailableDatasetTables",
    type=gql.Ref("DatasetTableSearchResult"),
    args=[
        gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="filter", type=gql.Ref("DatasetTableFilter")),
    ],
    resolver=list_available_cluster_dataset_tables,
)

listRedshiftClusterCopiedDatasetTables = gql.QueryField(
    name="listRedshiftClusterCopyEnabledTables",
    type=gql.Ref("DatasetTableSearchResult"),
    args=[
        gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="filter", type=gql.Ref("DatasetTableFilter")),
    ],
    resolver=list_copy_enabled_dataset_tables,
)

getRedshiftClusterDatabaseCredentials = gql.QueryField(
    name="getRedshiftClusterDatabaseCredentials",
    args=[gql.Argument(name="clusterUri", type=gql.NonNullableType(gql.String))],
    resolver=get_datahubdb_credentials,
    type=gql.Ref("RedshiftClusterCredentials"),
)
