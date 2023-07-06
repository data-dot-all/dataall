from dataall.base.api import gql
from dataall.api.constants import SortDirection, GraphQLEnumMapper

ModifyDatasetTableInput = gql.InputType(
    name='ModifyDatasetTableInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument('prefix', gql.String),
        gql.Argument('description', gql.String),
        gql.Argument('tags', gql.ArrayType(gql.String)),
        gql.Argument('terms', gql.ArrayType(gql.String)),
        gql.Argument('topics', gql.ArrayType(gql.String)),
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
