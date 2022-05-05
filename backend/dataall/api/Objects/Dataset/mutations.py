from ... import gql
from .input_types import (ImportDatasetInput, ModifyDatasetInput,
                          NewDatasetInput)
from .resolvers import *

createDataset = gql.MutationField(
    name="createDataset",
    args=[gql.Argument(name="input", type=gql.NonNullableType(NewDatasetInput))],
    type=gql.Ref("Dataset"),
    resolver=create_dataset,
    test_scope="Dataset",
)

updateDataset = gql.MutationField(
    name="updateDataset",
    args=[
        gql.Argument(name="datasetUri", type=gql.String),
        gql.Argument(name="input", type=ModifyDatasetInput),
    ],
    type=gql.Ref("Dataset"),
    resolver=update_dataset,
    test_scope="Dataset",
)

syncTables = gql.MutationField(
    name="syncTables",
    args=[gql.Argument(name="datasetUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("DatasetTableSearchResult"),
    resolver=sync_tables,
)


generateDatasetAccessToken = gql.MutationField(
    name="generateDatasetAccessToken",
    args=[gql.Argument(name="datasetUri", type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=generate_dataset_access_token,
)


saveDatasetSummary = gql.MutationField(
    name="saveDatasetSummary",
    args=[
        gql.Argument(name="datasetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="content", type=gql.String),
    ],
    type=gql.Boolean,
    resolver=save_dataset_summary,
)


deleteDataset = gql.MutationField(
    name="deleteDataset",
    args=[
        gql.Argument(name="datasetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="deleteFromAWS", type=gql.Boolean),
    ],
    resolver=delete_dataset,
    type=gql.Boolean,
)


importDataset = gql.MutationField(
    name="importDataset",
    args=[gql.Argument(name="input", type=ImportDatasetInput)],
    type=gql.Ref("Dataset"),
    resolver=import_dataset,
    test_scope="Dataset",
)

publishDatasetUpdate = gql.MutationField(
    name="publishDatasetUpdate",
    args=[
        gql.Argument(name="datasetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="s3Prefix", type=gql.NonNullableType(gql.String)),
    ],
    resolver=publish_dataset_update,
    type=gql.Boolean,
)

StartGlueCrawler = gql.MutationField(
    name="startGlueCrawler",
    args=[
        gql.Argument(name="datasetUri", type=gql.String),
        gql.Argument(name="input", type=gql.Ref("CrawlerInput")),
    ],
    resolver=start_crawler,
    type=gql.Ref("GlueCrawler"),
)
