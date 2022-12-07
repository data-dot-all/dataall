from common.api.gql.graphql_enum import GraphqlEnum as Enum
from common.api.gql.graphql_input import InputType
from common.api.gql.graphql_scalar import Scalar
from common.api.gql.graphql_type import ObjectType
from common.api.gql.ref import Ref
from common.api.gql.thunk import Thunk


class TypeModifier:
    def __init__(self, of):
        self.of_type = of

    @property
    def name(self):
        return self.of_type.name


def modifier_factory(template):
    class Modifier(TypeModifier):
        def __init__(self, of):
            TypeModifier.__init__(self, of)

        def gql(self):
            if isinstance(self.of_type, Ref):
                return template(name=self.of_type.name)
            elif isinstance(self.of_type, Enum):
                return template(name=self.of_type.name)
            elif isinstance(self.of_type, Scalar):
                return template(name=self.of_type.gql())
            elif isinstance(self.of_type, InputType):
                return template(name=self.of_type.name)
            elif isinstance(self.of_type, ObjectType):
                return template(self.of_type.name)
            elif isinstance(self.of_type, TypeModifier):
                return template(self.of_type.gql())
            elif isinstance(self.of_type, Thunk):
                return template(self.of_type.target.name)
            else:
                raise Exception('Cant gql ')

    return Modifier


ArrayType = modifier_factory(lambda name: f'[{name}]')
NonNullableType = modifier_factory(lambda name: f'{name}!')
