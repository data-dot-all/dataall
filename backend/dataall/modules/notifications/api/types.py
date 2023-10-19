from dataall.base.api import gql


Notification = gql.ObjectType(
    name='Notification',
    fields=[
        gql.Field(name='notificationUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='type', type=gql.String),
        gql.Field(name='message', type=gql.String),
        gql.Field(name='username', type=gql.NonNullableType(gql.String)),
        gql.Field(name='target_uri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='is_read', type=gql.Boolean),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
    ],
)


NotificationSearchResult = gql.ObjectType(
    name='NotificationSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(Notification)),
    ],
)
