from ... import gql

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
    fields=[
        gql.Field(name='cells', type=gql.ArrayType(gql.Ref('AthenaResultRecordCell')))
    ],
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
        gql.Field(
            name='columns', type=gql.ArrayType(gql.Ref('AthenaResultColumnDescriptor'))
        ),
        gql.Field(name='rows', type=gql.ArrayType(gql.Ref('AthenaResultRecord'))),
    ],
)
