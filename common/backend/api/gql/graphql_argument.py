from common.api.gql.graphql_enum import GraphqlEnum as Enum
from common.api.gql.graphql_input import InputType
from common.api.gql.graphql_scalar import Scalar
from common.api.gql.graphql_type_modifiers import ArrayType, NonNullableType
from common.api.gql.ref import Ref
from common.api.gql.thunk import Thunk
from common.api.gql.utils import get_named_type


class Argument:
    def __init__(self, name, type):
        self.name = name
        if isinstance(get_named_type(type), (Scalar, InputType, Ref, Enum)):
            self.type = type  # get_named_type(type)
        else:
            raise Exception('Invalid Argument Type')

    def gql(self):
        if isinstance(self.type, Enum):
            return f'{self.name} : {self.type.name}'
        elif isinstance(self.type, Ref):
            return f'{self.name} : {self.type.name}'
        elif isinstance(self.type, Scalar):
            return f'{self.name} : {self.type.name}'
        elif isinstance(self.type, InputType):
            return f'{self.name} : {self.type.name}'
        elif isinstance(self.type, (ArrayType, NonNullableType)):
            return f'{self.name} : {self.type.gql()}'
        elif isinstance(self.type, Thunk):
            return f'{self.name} : {self.type.target.gql()}'
