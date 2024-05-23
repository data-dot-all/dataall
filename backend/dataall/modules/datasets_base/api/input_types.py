from dataall.base.api import gql
from dataall.base.api.constants import SortDirection
from dataall.modules.datasets_base.services.datasets_enums import DatasetSortField


DatasetSortCriteria = gql.InputType(
    name='DatasetSortCriteria',
    arguments=[
        gql.Argument(name='field', type=gql.NonNullableType(DatasetSortField.toGraphQLEnum())),
        gql.Argument(name='direction', type=SortDirection.toGraphQLEnum()),
    ],
)


DatasetFilter = gql.InputType(
    name='DatasetFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('roles', gql.ArrayType(gql.Ref('DatasetRole'))),
        gql.Argument('InProject', gql.String),
        gql.Argument('notInProject', gql.String),
        gql.Argument('displayArchived', gql.Boolean),
        gql.Argument('sort', gql.ArrayType(DatasetSortCriteria)),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
