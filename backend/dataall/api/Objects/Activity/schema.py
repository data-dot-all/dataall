from ... import gql

Activity = gql.ObjectType(
    name="Activity",
    fields=[
        gql.Field(name="activityUri", type=gql.ID),
        gql.Field(name="owner", type=gql.NonNullableType(gql.String)),
        gql.Field(name="target", type=gql.String),
        gql.Field(name="targetType", type=gql.String),
        gql.Field(name="targetUri", type=gql.String),
        gql.Field(name="created", type=gql.String),
        gql.Field(name="action", type=gql.String),
        gql.Field(name="summary", type=gql.String),
    ],
)


ActivitySearchResult = gql.ObjectType(
    name="ActivitySearchResult",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(Activity)),
    ],
)
