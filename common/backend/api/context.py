from enum import Enum
from argparse import Namespace
from ariadne import (
    EnumType,
    MutationType,
    ObjectType,
    UnionType,
    QueryType,
    gql as GQL,
    make_executable_schema,
)

from backend.api import gql


class GraphQLEnumMapper(Enum):
    @classmethod
    def toGraphQLEnum(cls):
        return gql.GraphqlEnum(name=cls.__name__, values=cls)

    @classmethod
    def to_value(cls, label):
        for c in cls:
            if c.name == label:
                return c.value
        return None

    @classmethod
    def to_label(cls, value):
        for c in cls:
            if getattr(cls, c.name).value == value:
                return c.name
        return None


class Context:
    def __init__(
        self,
        engine=None,
        es=None,
        username=None,
        groups=None,
        cdkproxyurl=None,
    ):
        self.engine = engine
        self.es = es
        self.username = username
        self.groups = groups
        self.cdkproxyurl = cdkproxyurl


def bootstrap():
    classes = {
        gql.ObjectType: [],
        gql.QueryField: [],
        gql.MutationField: [],
        gql.Enum: [],
        gql.Union: [],
        gql.InputType: [],
    }

    Query = gql.ObjectType(name='Query', fields=classes[gql.QueryField])

    Mutation = gql.ObjectType(name='Mutation', fields=classes[gql.MutationField])
    print("printing enum loop")
    for enumclass in GraphQLEnumMapper.__subclasses__():
        # Gets all Enums from constants.py
        enumclass.toGraphQLEnum()
        print(f"inside enum.class: {enumclass}")

    print("printing classes loop")
    for cls in classes.keys():
        print(f"inside loop, class: {cls}")
        print(f"inside loop, class: {cls.class_instances['default']}")
        for name in cls.class_instances['default'].keys():
            if cls.get_instance(name):
                classes[cls].append(cls.get_instance(name))
            else:
                raise Exception(f'Unknown Graphql Type :`{name}`')

    schema = gql.Schema(
        types=classes[gql.ObjectType],
        inputs=classes[gql.InputType],
        enums=classes[gql.Enum],
        unions=classes[gql.Union],
    )
    return schema


def save():
    schema = bootstrap()
    with open('schema.graphql', 'w') as f:
        f.write(schema.gql())


def resolver_adapter(resolver):
    def adapted(obj, info, **kwargs):
        response = resolver(
            context=Namespace(
                engine=info.context['engine'],
                es=info.context['es'],
                username=info.context['username'],
                groups=info.context['groups'],
                schema=info.context['schema'],
                cdkproxyurl=info.context['cdkproxyurl'],
            ),
            source=obj or None,
            **kwargs,
        )
        return response

    return adapted


def get_executable_schema():
    schema = bootstrap()
    _types = []
    for _type in schema.types:
        if _type.name == 'Query':
            query = QueryType()
            _types.append(query)
            for field in _type.fields:
                if field.resolver:
                    query.field(field.name)(resolver_adapter(field.resolver))
        elif _type.name == 'Mutation':
            mutation = MutationType()
            _types.append(mutation)
            for field in _type.fields:
                if field.resolver:
                    mutation.field(field.name)(resolver_adapter(field.resolver))
        else:
            object_type = ObjectType(name=_type.name)

            for field in _type.fields:
                if field.resolver:
                    object_type.field(field.name)(resolver_adapter(field.resolver))
            _types.append(object_type)

    _enums = []
    for enum in schema.enums:
        d = {}
        for k in enum.values:
            d[k.name] = k.value
        _enums.append(EnumType(enum.name, d))

    _unions = []
    for union in schema.unions:
        _unions.append(UnionType(union.name, union.resolver))

    type_defs = GQL(schema.gql(with_directives=False))
    executable_schema = make_executable_schema(type_defs, *(_types + _enums + _unions))
    return executable_schema



