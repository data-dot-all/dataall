from dataall.base.api import gql
from dataall.modules.worksheets.api.resolvers import resolve_user_role

AthenaResultColumnDescriptor = gql.ObjectType(
    name='AthenaResultColumnDescriptor',
    fields=[
        gql.Field(name='columnName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='typeName', type=gql.NonNullableType(gql.String)),
    ],
)


AthenaResultRecordCell = gql.ObjectType(
    name='AthenaResultRecordCell',
    fields=[
        gql.Field(name='value', type=gql.String),
        gql.Field(name='typeName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='columnName', type=gql.NonNullableType(gql.String)),
    ],
)

AthenaResultRecord = gql.ObjectType(
    name='AthenaResultRecord',
    fields=[gql.Field(name='cells', type=gql.ArrayType(gql.Ref('AthenaResultRecordCell')))],
)


AthenaQueryResult = gql.ObjectType(
    name='AthenaQueryResult',
    fields=[
        gql.Field(name='Error', type=gql.String),
        gql.Field(name='OutputLocation', type=gql.String),
        gql.Field(name='AthenaQueryId', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='ElapsedTimeInMs', type=gql.Integer),
        gql.Field(name='DataScannedInBytes', type=gql.Integer),
        gql.Field(name='Status', type=gql.String),
        gql.Field(name='columns', type=gql.ArrayType(gql.Ref('AthenaResultColumnDescriptor'))),
        gql.Field(name='rows', type=gql.ArrayType(gql.Ref('AthenaResultRecord'))),
    ],
)


Worksheet = gql.ObjectType(
    name='Worksheet',
    fields=[
        gql.Field(name='worksheetUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='sqlBody', type=gql.String),
        gql.Field(name='chartConfig', type=gql.Ref('WorksheetChartConfig')),
        gql.Field(name='created', type=gql.NonNullableType(gql.String)),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='owner', type=gql.NonNullableType(gql.String)),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(
            name='lastSavedQueryResult',
            type=gql.Ref('AthenaQueryResult'),
        ),
        gql.Field(
            name='userRoleForWorksheet',
            type=gql.Ref('WorksheetRole'),
            resolver=resolve_user_role,
        ),
    ],
)


Worksheets = gql.ObjectType(
    name='Worksheets',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(gql.Ref('Worksheet'))),
    ],
)


WorksheetQueryResult = gql.ObjectType(
    name='WorksheetQueryResult',
    fields=[
        gql.Field(name='worksheetQueryResultUri', type=gql.ID),
        gql.Field(name='queryType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='sqlBody', type=gql.NonNullableType(gql.String)),
        gql.Field(name='AthenaQueryId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='region', type=gql.NonNullableType(gql.String)),
        gql.Field(name='AwsAccountId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='AthenaOutputBucketName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='AthenaOutputKey', type=gql.NonNullableType(gql.String)),
        gql.Field(name='timeElapsedInSecond', type=gql.NonNullableType(gql.Integer)),
        gql.Field(name='created', type=gql.NonNullableType(gql.String)),
    ],
)


WorksheetChartDimension = gql.ObjectType(
    name='WorksheetChartDimension',
    fields=[gql.Field(name='columnName', type=gql.NonNullableType(gql.String))],
)

WorksheetChartMeasure = gql.ObjectType(
    name='WorksheetChartMeasure',
    fields=[
        gql.Field(name='columnName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='aggregationName', type=gql.String),
    ],
)

WorksheetChartConfig = gql.ObjectType(
    name='WorksheetChartConfig',
    fields=[
        gql.Field(name='AthenaQueryId', type=gql.String),
        gql.Field(name='dimensions', type=gql.ArrayType(gql.Ref('WorksheetChartDimension'))),
        gql.Field(name='measures', type=gql.ArrayType(gql.Ref('WorksheetChartMeasure'))),
    ],
)
