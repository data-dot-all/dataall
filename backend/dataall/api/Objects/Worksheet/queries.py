from ... import gql
from .resolvers import *

getWorksheet = gql.QueryField(
    name="getWorksheet",
    type=gql.Ref("Worksheet"),
    resolver=get_worksheet,
    args=[gql.Argument(name="worksheetUri", type=gql.NonNullableType(gql.String))],
)


listWorksheets = gql.QueryField(
    name="listWorksheets",
    resolver=list_worksheets,
    args=[gql.Argument(name="filter", type=gql.Ref("WorksheetFilter"))],
    type=gql.Ref("Worksheets"),
)


"""

getWorksheetChart = gql.QueryField(
    name="getWorksheetChart",
    resolver=get_worksheet_chart,
    type=gql.Ref("WorksheetChart"),
    args=[
        gql.Argument(name="worksheetChartUri", type=gql.NonNullableType(gql.String))
    ]
)

getWorksheetQuery= gql.QueryField(
    name="getWorksheetQuery",
    resolver=get_worksheet_query,
    type=gql.Ref("WorksheetQuery"),
    args=[
        gql.Argument(name="worksheetQueryUri", type=gql.NonNullableType(gql.String))
    ]
)
"""

pollWorksheetQuery = gql.QueryField(
    name="pollWorksheetQuery",
    resolver=poll_query,
    args=[
        gql.Argument(name="worksheetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="AthenaQueryId", type=gql.String),
    ],
    type=gql.Ref("AthenaQueryResult"),
)
