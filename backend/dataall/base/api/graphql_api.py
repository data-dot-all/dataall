import inspect
from dataclasses import dataclass
from typing import get_type_hints, Optional

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
    term: str
    page: int
    pageSize: int


_scalars = {
    str: gql.NonNullableType(gql.String),
    Optional[str]: gql.String,
    int: gql.NonNullableType(gql.Integer),
    Optional[int]: gql.Integer,
    float: gql.NonNullableType(gql.Number),
    Optional[float]: gql.Number,
    bool: gql.NonNullableType(gql.Boolean),
    Optional[bool]: gql.Boolean,
}

_object_names = set()

_objects = {}


def _get_arguments_count(fn):
    signature = inspect.signature(fn)
    return len(signature.parameters)


def _resolve_ref(ref_type):
    ref_name = _objects.get(ref_type, None)
    if not ref_name:
        raise ValueError(f"No reference with name {ref_name}")


def _resolve_type(args_type):
    if issubclass(args_type, gql.ObjectType):
        return gql.Ref(args_type)
    if issubclass(args_type, gql.InputType):
        return gql.Ref(args_type)
    stype = _scalars.get(args_type, None)
    if stype:
        return stype

    return None


def _process_api_func(name, field):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        hints = get_type_hints(fn)
        num_args = _get_arguments_count(fn)

        if "return" not in hints:
            raise ValueError(f"Function {fn.__name__} doesn't specify the return type")

        if len(hints) != num_args + 1:
            raise ValueError(f"Function {fn.__name__} marked as GraphQL API, "
                             f"but don't specify types for all parameters")
        gql_args = []
        return_type = None
        for hint, value in hints.items():
            gql_type = _resolve_type(value)
            if not gql_type:
                raise ValueError(f"Function {fn.__name__}  takes/returns not a GraphQL type!")

            if hint != 'return':
                gql_args.append(gql.Argument(name=hint, type=gql_type))
            else:
                return_type = gql_type

        def decorated(*args, **kwargs):
            return fn(*args, **kwargs)

        field(
            name=name,
            args=gql_args,
            type=return_type,
            resolver=fn_decorator,
        )

        return fn_decorator(decorated)
    return decorator


def api_query(name: str):
    return _process_api_func(name, gql.QueryField)


def api_mutation(name: str):
    return _process_api_func(name, gql.MutationField)


def _process_api_class(name):
    if name in _object_names:
        raise ValueError(f"The object {name} already exists in the schema")
    _object_names.add(name)

    def class_decorator(cls):
        _objects[cls] = name

        hints = get_type_hints(cls)
        for hint, value in hints.items():
            gql_type = _resolve_type(value)
            if not gql_type:
                raise ValueError(f"Class {cls.__name__}  has unknown GraphQL type for {hint}")

        return cls
    return class_decorator


def api_object(name: str):
    return _process_api_class(name)


def api_input(name: str):
    return _process_api_class(name)