from ... import gql
from ....api.constants import SortDirection, GraphQLEnumMapper


NewDatasetTableInput = gql.InputType(
    name='NewDatasetTableInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('name', gql.NonNullableType(gql.String)),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('config', gql.String),
        gql.Argument('region', gql.String),
    ],
)

ModifyDatasetTableInput = gql.InputType(
    name='ModifyDatasetTableInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('prefix', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('terms', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.ArrayType(gql.String)),
        gql.Argument('lfTagKey', gql.ArrayType(gql.String)),
        gql.Argument('lfTagValue', gql.ArrayType(gql.String))
    ],
)


class DatasetSortField(GraphQLEnumMapper):
    created = 'created'
    updated = 'updated'
    label = 'label'


DatasetSortCriteria = gql.InputType(
    name='DatasetSortCriteria',
    arguments=[
        gql.Argument(name='field', type=DatasetSortField.toGraphQLEnum()),
        gql.Argument(name='direction', type=SortDirection.toGraphQLEnum()),
    ],
)

DatasetTableFilter = gql.InputType(
    name='DatasetTableFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('sort', gql.ArrayType(DatasetSortCriteria)),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
