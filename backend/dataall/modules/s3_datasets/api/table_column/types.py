from dataall.base.api import gql
from dataall.modules.s3_datasets.api.table_column.resolvers import resolve_terms


DatasetTableColumn = gql.ObjectType(
    name='DatasetTableColumn',
    fields=[
        gql.Field(name='tableUri', type=gql.ID),
        gql.Field(name='columnUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='GlueDatabaseName', type=gql.String),
        gql.Field(name='GlueTableName', type=gql.String),
        gql.Field(name='typeName', type=gql.String),
        gql.Field(name='columnType', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='classification', type=gql.String),
        gql.Field(name='topics', type=gql.ArrayType(gql.String)),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='terms', type=gql.Ref('TermLinkSearchResults'), resolver=resolve_terms),
    ],
)


DatasetTableColumnSearchResult = gql.ObjectType(
    name='DatasetTableColumnSearchResult',
    fields=[
        gql.Field(name='nodes', type=gql.ArrayType(DatasetTableColumn)),
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
