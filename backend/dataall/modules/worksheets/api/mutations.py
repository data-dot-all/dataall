from dataall.base.api import gql
from dataall.modules.worksheets.api.resolvers import create_worksheet, delete_worksheet, update_worksheet


createWorksheet = gql.MutationField(
    name='createWorksheet',
    args=[gql.Argument(name='input', type=gql.Ref('NewWorksheetInput'))],
    type=gql.Ref('Worksheet'),
    resolver=create_worksheet,
)

updateWorksheet = gql.MutationField(
    name='updateWorksheet',
    resolver=update_worksheet,
    args=[
        gql.Argument(name='worksheetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('UpdateWorksheetInput')),
    ],
    type=gql.Ref('Worksheet'),
)

deleteWorksheet = gql.MutationField(
    name='deleteWorksheet',
    resolver=delete_worksheet,
    args=[
        gql.Argument(name='worksheetUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
)
