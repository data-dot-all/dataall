from dataall.base.api.gql import ObjectType
from dataall.base.api.gql.graphql_type_modifiers import NonNullableType
from dataall.base.api.gql.graphql_scalar import String


class Interface(ObjectType):
    def __init__(self, name, fields):
        ObjectType.__init__(self, name, fields=fields)

    def gql(self, with_directives=True):
        n = '\n'
        return f'interface {self.name} {{ {n} {n.join([f.gql(with_directives=False) for f in self.fields])}{n} }}{n}'


if __name__ == '__main__':
    from .graphql_field import Field
    from .graphql_type_modifiers import *
    from .graphql_scalar import *

    Searchable = Interface(
        name='Searchable',
        fields=[
            Field(name='uri', type=NonNullableType(String)),
            Field(name='resource_name', type=NonNullableType(String)),
            Field(name='name', type=NonNullableType(String)),
        ],
    )

    print(Searchable.gql())
