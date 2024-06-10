from .graphql_enum import GraphqlEnum as Enum
from .graphql_input import InputType
from .graphql_scalar import Scalar
from .graphql_type_modifiers import ArrayType, NonNullableType
from .ref import Ref
from .thunk import Thunk
from .utils import get_named_type


class Argument:
    def __init__(self, name, type, description=''):
        self.name = name
        self.description = description
        if isinstance(get_named_type(type), (Scalar, InputType, Ref, Enum)):
            self.type = type  # get_named_type(type)
        else:
            raise Exception('Invalid Argument Type')

    def gql(self):
        description_str = f'"""{self.description}"""\n' if self.description else ''

        if isinstance(self.type, Enum):
            return f'{description_str}{self.name} : {self.type.name}'
        elif isinstance(self.type, Ref):
            return f'{description_str}{self.name} : {self.type.name}'
        elif isinstance(self.type, Scalar):
            return f'{description_str}{self.name} : {self.type.name}'
        elif isinstance(self.type, InputType):
            return f'{description_str}{self.name} : {self.type.name}'
        elif isinstance(self.type, (ArrayType, NonNullableType)):
            return f'{description_str}{self.name} : {self.type.gql()}'
        elif isinstance(self.type, Thunk):
            return f'{description_str}{self.name} : {self.type.target.gql()}'
