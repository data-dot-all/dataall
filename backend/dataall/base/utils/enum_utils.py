from dataall.base.api import gql


def generate_enum_resolver(enum_class):
    def resolver(context, source):
        return [{'name': item.name, 'value': str(item.value)} for item in enum_class]

    return resolver


EnumItem = gql.ObjectType(
    name='EnumItem',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='value', type=gql.String),
    ],
)


def generate_enum_query(enum_class, test_scope):
    return gql.QueryField(
        name=enum_class.__name__,
        type=gql.ArrayType(EnumItem),
        resolver=generate_enum_resolver(enum_class),
        test_scope=test_scope,
    )
