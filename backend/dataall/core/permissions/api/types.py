from dataall.base.api import gql
from dataall.core.permissions.api.enums import PermissionType


def resolve_enum(context, source: PermissionType):
    return source.type.name if source.type else PermissionType.TENANT.name


Permission = gql.ObjectType(
    name='Permission',
    fields=[
        gql.Field(name='permissionUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='type', type=gql.String, resolver=resolve_enum),
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='description', type=gql.NonNullableType(gql.String)),
    ],
)

DescribedPermission = gql.ObjectType(
    name='DescribedPermission',
    fields=[
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='description', type=gql.NonNullableType(gql.String)),
    ],
)


PermissionSearchResult = gql.ObjectType(
    name='PermissionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(Permission)),
    ],
)


Tenant = gql.ObjectType(
    name='Tenant',
    fields=[
        gql.Field(name='tenantUri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='created', type=gql.String),
    ],
)
