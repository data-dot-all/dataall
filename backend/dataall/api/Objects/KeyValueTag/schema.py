from ... import gql

KeyValueTag = gql.ObjectType(
    name='KeyValueTag',
    fields=[
        gql.Field(name='tagUri', type=gql.ID),
        gql.Field(name='targetType', type=gql.String),
        gql.Field(name='targetUri', type=gql.String),
        gql.Field(name='key', type=gql.String),
        gql.Field(name='value', type=gql.String),
        gql.Field(name='cascade', type=gql.Boolean),
    ],
)
