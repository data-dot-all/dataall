import inspect
from dataclasses import dataclass, fields
from enum import Enum
from typing import get_type_hints

from dataall.base.api import gql
from dataall.base.utils.decorator_utls import process_func


@dataclass
class Page(gql.ObjectType):
    count: int
    page: int
    pages: int
    hasNext: bool
    hasPrevious: bool


@dataclass
class PageFilter(gql.InputType):
    term: str = None
    page: int = 5
    pageSize: int = 20


class SerializedObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


_scalars = {
    str: gql.String,
    int: gql.Integer,
    float: gql.Number,
    bool: gql.Boolean,
}

_object_names = set()

_objects = {}


def _resolve_ref(ref_type):
    ref_name = _objects.get(ref_type, None)
    if not ref_name:
        raise ValueError(f"No reference with name {ref_name}")


def _resolve_type(arg_type):
    if isinstance(arg_type, list):
        return gql.ArrayType(_resolve_type(arg_type[0]))
    if arg_type == gql.ID or isinstance(arg_type, gql.Ref):
        return arg_type
    if issubclass(arg_type, Enum):
        return gql.Enum(name=arg_type.__name__, values=arg_type)
    if issubclass(arg_type, gql.ObjectType) or issubclass(arg_type, gql.InputType):
        return gql.Ref(_objects[arg_type])
    return _scalars.get(arg_type)


def _has_default_value(cls, field_name):
    for field_info in fields(cls):
        if field_info.name == field_name:
            return field_info.default is not field_info.default_factory
    return False


def _process_api_func(name, field):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        hints = get_type_hints(fn)
        signature = inspect.signature(fn)
        num_args = len(signature.parameters)

        if "return" not in hints:
            raise ValueError(f"Function {fn.__name__} doesn't specify the return type")

        if len(hints) != num_args + 1:
            raise ValueError(f"Function {fn.__name__} marked as GraphQL API, "
                             f"but don't specify types for all parameters")
        gql_args = []
        return_type = None

        parameters = signature.parameters
        for hint, value in hints.items():
            gql_type = _resolve_type(value)
            if not gql_type:
                raise ValueError(f"Function {fn.__name__}  takes/returns not a GraphQL type!")

            if hint != 'return':
                param = parameters[hint]
                has_default = param.default is not inspect.Parameter.empty
                gql_args.append(
                    gql.Argument(
                        name=hint,
                        type=gql_type if has_default else gql.NonNullableType(gql_type)
                    )
                )
            else:
                return_type = gql_type

        def decorated(*args, **kwargs):
            return fn(*args, **kwargs)

        field(
            name=name,
            args=gql_args if gql_args else None,
            type=return_type,
            resolver=fn_decorator(decorated),
            api_version=2,
        )

        return fn_decorator(decorated)
    return decorator


def _process_api_class(name, object_factory):
    if name in _object_names:
        raise ValueError(f"The object {name} already exists in the schema")
    _object_names.add(name)

    def class_decorator(cls):
        _objects[cls] = name

        hints = get_type_hints(cls)
        gql_args = []

        for hint, value in hints.items():
            gql_type = _resolve_type(value)
            if not gql_type:
                raise ValueError(f"Class {cls.__name__}  has unknown GraphQL type for {hint}")

            has_default = _has_default_value(cls, hint)
            gql_args.append((hint, gql_type if has_default else gql.NonNullableType(gql_type)))

        object_factory(gql_args)

        return cls
    return class_decorator


def api_query(name: str):
    return _process_api_func(name, gql.QueryField)


def api_mutation(name: str):
    return _process_api_func(name, gql.MutationField)


def api_object(name: str):
    def gql_object_factory(hints):
        return gql.ObjectType(
            name=name,
            fields=[gql.Field(name=hint_name, type=hint_type) for hint_name, hint_type in hints]
        )

    return _process_api_class(name, gql_object_factory)


def api_input(name: str):
    def gql_input_type_factory(hints):
        return gql.InputType(
            name=name,
            arguments=[gql.Argument(name=hint_name, type=hint_type) for hint_name, hint_type in hints]
        )

    return _process_api_class(name, gql_input_type_factory)
