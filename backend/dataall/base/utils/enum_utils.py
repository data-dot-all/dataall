from dataall.base.api import gql
from dataall.base.api.constants import GraphQLEnumMapper


def enum_resolver(context, source, enums_names):
    result = []
    for enum_class in GraphQLEnumMapper.__subclasses__():
        if enum_class.__name__ in enums_names:
            result.append(
                {
                    'name': enum_class.__name__,
                    'items': [{'name': item.name, 'value': str(item.value)} for item in enum_class],
                }
            )
    return result


EnumItem = gql.ObjectType(
    name='EnumItem',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='value', type=gql.String),
    ],
)

EnumResult = gql.ObjectType(
    name='EnumResult',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='items', type=gql.ArrayType(EnumItem)),
    ],
)


def generate_enum_query():
    return gql.QueryField(
        name='queryEnum',
        args=[gql.Argument(name='enums_names', type=gql.ArrayType(gql.String))],
        type=gql.ArrayType(EnumResult),
        resolver=enum_resolver,
        test_scope='Enums',
    )
