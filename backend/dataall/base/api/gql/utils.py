import types

from .graphql_type_modifiers import ArrayType, Enum, InputType, NonNullableType, ObjectType, Scalar
from .ref import Ref
from .thunk import Thunk


def get_named_type(type):
    if isinstance(type, Enum):
        return type
    if isinstance(type, Ref):
        return type
    if isinstance(type, ObjectType):
        return type
    elif isinstance(type, InputType):
        return type
    elif isinstance(type, NonNullableType):
        return get_named_type(type.of_type)
    elif isinstance(type, ArrayType):
        return get_named_type(type.of_type)
    elif isinstance(type, Scalar):
        return type
    elif isinstance(type, types.FunctionType):
        thunk_type = type()
        return get_named_type(thunk_type)
    elif isinstance(type, Thunk):
        thunk_type = type.target
        return get_named_type(thunk_type)
    else:
        raise Exception("Don't know this type")
