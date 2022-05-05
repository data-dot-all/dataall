from ... import gql
from .resolvers import *


createWorksheet = gql.MutationField(
    name="createWorksheet",
    args=[gql.Argument(name="input", type=gql.Ref("NewWorksheetInput"))],
    type=gql.Ref("Worksheet"),
    resolver=create_worksheet,
)

updateWorksheet = gql.MutationField(
    name="updateWorksheet",
    resolver=update_worksheet,
    args=[
        gql.Argument(name="worksheetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="input", type=gql.Ref("UpdateWorksheetInput")),
    ],
    type=gql.Ref("Worksheet"),
)

shareWorksheet = gql.MutationField(
    name="shareWorksheet",
    resolver=share_worksheet,
    args=[
        gql.Argument(name="worksheetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="input", type=gql.Ref("WorksheetShareInput")),
    ],
    type=gql.Ref("WorksheetShare"),
)

updateShareWorksheet = gql.MutationField(
    name="updateShareWorksheet",
    resolver=update_worksheet_share,
    args=[
        gql.Argument(name="worksheetShareUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="canEdit", type=gql.NonNullableType(gql.Boolean)),
    ],
    type=gql.Ref("WorksheetShare"),
)

deleteShareWorksheet = gql.MutationField(
    name="deleteShareWorksheet",
    resolver=remove_worksheet_share,
    args=[
        gql.Argument(name="worksheetShareUri", type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
)

startWorksheetQuery = gql.MutationField(
    name="startWorksheetQuery",
    resolver=start_query,
    args=[
        gql.Argument(name="worksheetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="input", type=gql.Ref("WorksheetQueryInput")),
    ],
    type=gql.Ref("AthenaQueryResult"),
)

deleteWorksheet = gql.MutationField(
    name="deleteWorksheet",
    resolver=delete_worksheet,
    args=[
        gql.Argument(name="worksheetUri", type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
)
