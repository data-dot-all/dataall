from .graphql_type import ObjectType


class Interface(ObjectType):
    def __init__(self, name, fields):
        ObjectType.__init__(self, name, fields=fields)

    def gql(self, with_directives=True):
        n = "\n"
        return f"interface {self.name} {{ {n} {n.join([f.gql(with_directives=False) for f in self.fields])}{n} }}{n}"


if __name__ == "__main__":
    from .graphql_field import Field
    from .graphql_scalar import *
    from .graphql_type_modifiers import *

    Searchable = Interface(
        name="Searchable",
        fields=[
            Field(name="uri", type=NonNullableType(String)),
            Field(name="resource_name", type=NonNullableType(String)),
            Field(name="name", type=NonNullableType(String)),
        ],
    )

    print(Searchable.gql())
