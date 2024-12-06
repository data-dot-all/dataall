from dataall.modules.s3_datasets.api.table_column.resolvers import list_table_columns
from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table.resolvers import (
    resolve_dataset,
    get_glue_table_properties,
    resolve_glossary_terms,
    get_dataset_table_restricted_information,
)

TablePermission = gql.ObjectType(
    name='TablePermission',
    fields=[
        gql.Field(name='userName', type=gql.String),
        gql.Field(name='created', type=gql.String),
    ],
)

TablePermissionSearchResult = gql.ObjectType(
    name='TablePermissionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(TablePermission)),
    ],
)
DatasetTableRestrictedInformation = gql.ObjectType(
    name='DatasetTableRestrictedInformation',
    fields=[
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='GlueDatabaseName', type=gql.String),
        gql.Field(name='GlueTableName', type=gql.String),
        gql.Field(name='S3Prefix', type=gql.String),
    ],
)

DatasetTable = gql.ObjectType(
    name='DatasetTable',
    fields=[
        gql.Field(name='tableUri', type=gql.ID),
        gql.Field(name='datasetUri', type=gql.String),
        gql.Field(name='dataset', type=gql.Ref('Dataset'), resolver=resolve_dataset),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='admins', type=gql.ArrayType(gql.String)),
        gql.Field(name='LastGlueTableStatus', type=gql.String),
        gql.Field(name='GlueTableConfig', type=gql.String),
        gql.Field(
            name='restricted', type=DatasetTableRestrictedInformation, resolver=get_dataset_table_restricted_information
        ),
        gql.Field(
            name='GlueTableProperties',
            type=gql.String,
            resolver=get_glue_table_properties,
        ),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='userRoleForTable', type=gql.Ref('DatasetRole')),
        gql.Field(name='stage', type=gql.String),
        gql.Field(
            name='columns',
            resolver=list_table_columns,
            type=gql.Ref('DatasetTableColumnSearchResult'),
        ),
        gql.Field(
            name='terms',
            type=gql.Ref('TermSearchResult'),
            resolver=resolve_glossary_terms,
        ),
    ],
)

DatasetTableSearchResult = gql.ObjectType(
    name='DatasetTableSearchResult',
    fields=[
        gql.Field(name='nodes', type=gql.ArrayType(DatasetTable)),
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)

DatasetTableDataFilter = gql.ObjectType(
    name='DatasetTableDataFilter',
    fields=[
        gql.Field(name='filterUri', type=gql.String),
        gql.Field(name='tableUri', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='filterType', type=gql.String),
        gql.Field(name='includedCols', type=gql.ArrayType(gql.String)),
        gql.Field(name='rowExpression', type=gql.String),
    ],
)

DatasetTableDataFilterSearchResult = gql.ObjectType(
    name='DatasetTableDataFilterSearchResult',
    fields=[
        gql.Field(name='nodes', type=gql.ArrayType(DatasetTableDataFilter)),
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)

DatasetTableRecord = gql.ObjectType(name='DatasetTableRecord', fields=[gql.Field(name='data', type=gql.String)])

DatasetTableMetadataItem = gql.ObjectType(
    name='DatasetTableMetadataItem',
    fields=[
        gql.Field(name='Name', type=gql.String),
        gql.Field(name='Type', type=gql.String),
    ],
)

SharedDatasetTableItem = gql.ObjectType(
    name='SharedDatasetTableItem',
    fields=[
        gql.Field(name='tableUri', type=gql.String),
        gql.Field(name='GlueTableName', type=gql.String),
    ],
)
