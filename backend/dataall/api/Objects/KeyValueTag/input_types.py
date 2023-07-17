from ... import gql

KeyValueTagInput = gql.InputType(
    name='KeyValueTagInput',
    arguments=[
        gql.Argument(name='key', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='value', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='cascade', type=gql.NonNullableType(gql.Boolean)),
    ],
)

UpdateKeyValueTagsInput = gql.InputType(
    name='UpdateKeyValueTagsInput',
    arguments=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='tags', type=gql.ArrayType(gql.Ref('KeyValueTagInput'))),
    ],
)
