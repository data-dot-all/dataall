from dataall.base.api import gql

NewWorksheetInput = gql.InputType(
    name='NewWorksheetInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
    ],
)

UpdateWorksheetInput = gql.InputType(
    name='UpdateWorksheetInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='sqlBody', type=gql.String),
        gql.Argument(name='chartConfig', type=gql.Ref('WorksheetChartConfigInput')),
    ],
)


WorksheetChartInput = gql.InputType(
    name='WorksheetChartInput',
    arguments=[
        gql.Argument(name='chartConfig', type=gql.String),
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='description', type=gql.String),
    ],
)

WorksheetQueryInput = gql.InputType(
    name='WorksheetQueryInput',
    arguments=[
        gql.Argument(name='sqlBody', type=gql.String),
        gql.Argument(name='AthenaQueryId', type=gql.String),
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
    ],
)


WorksheetFilter = gql.InputType(
    name='WorksheetFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)


WorksheetDimensionInput = gql.InputType(
    name='WorksheetDimensionInput',
    arguments=[
        gql.Argument(name='columnName', type=gql.String),
    ],
)

WorksheetMeasureInput = gql.InputType(
    name='WorksheetMeasureInput',
    arguments=[
        gql.Argument(name='columnName', type=gql.String),
        gql.Argument(name='aggregationName', type=gql.String),
    ],
)


WorksheetChartConfigInput = gql.InputType(
    name='WorksheetChartConfigInput',
    arguments=[
        gql.Argument(name='chartType', type=gql.String),
        gql.Argument(name='dimensions', type=gql.ArrayType(gql.Ref('WorksheetDimensionInput'))),
        gql.Argument(name='measures', type=gql.ArrayType(gql.Ref('WorksheetMeasureInput'))),
    ],
)
