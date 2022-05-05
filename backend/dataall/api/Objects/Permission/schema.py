from .... import db
from ... import gql


def resolve_enum(context, source: db.models.Notification):
    return source.type.name if source.type else db.models.PermissionType.TENANT.name


Permission = gql.ObjectType(
    name="Permission",
    fields=[
        gql.Field(name="permissionUri", type=gql.NonNullableType(gql.String)),
        gql.Field(name="type", type=gql.String, resolver=resolve_enum),
        gql.Field(name="name", type=gql.NonNullableType(gql.String)),
        gql.Field(name="description", type=gql.NonNullableType(gql.String)),
    ],
)


PermissionSearchResult = gql.ObjectType(
    name="PermissionSearchResult",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(Permission)),
    ],
)
