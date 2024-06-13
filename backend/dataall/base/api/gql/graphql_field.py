import typing

from .graphql_argument import Argument
from .graphql_enum import GraphqlEnum
from .graphql_scalar import Scalar
from .graphql_type import ObjectType
from .graphql_type_modifiers import ArrayType, NonNullableType, TypeModifier
from .graphql_union_type import Union
from .ref import Ref
from .thunk import Thunk
from .utils import get_named_type


class Field:
    def __init__(
        self,
        name: str,
        type: object,
        args=None,
        directives=[],
        resolver=None,
        test_scope: str = None,
        test_cases: typing.List[str] = ['*'],
        description='',
    ):
        self.name: str = name
        self.type: typing.Union[Scalar, ObjectType, Ref] = type
        self.args: typing.List[Argument] = args
        self.directives = directives
        self.resolver: typing.Callable = resolver
        self.test_scope: str = test_scope
        self.test_cases: typing.List[str] = test_cases
        self.description = description

    def gql(self, with_directives=True) -> str:
        if isinstance(self.type, GraphqlEnum):
            t = self.type.name
        elif isinstance(self.type, Ref):
            t = self.type.name
        elif isinstance(self.type, Scalar):
            t = self.type.name
        elif isinstance(self.type, ObjectType):
            t = self.type.name
        elif isinstance(self.type, TypeModifier):
            t = self.type.gql()
        elif isinstance(self.type, Thunk):
            t = self.type.target.name
        elif isinstance(self.type, Union):
            t = self.type.name
        else:
            raise Exception(f'Invalid type for field `{self.name}`: {type(self.type)}')

        description_str = f'"""{self.description}"""\n' if self.description else ''

        args_list = []
        if self.args is not None:
            for a in self.args:
                if not isinstance(a, Argument):
                    raise Exception(f'Found wrong argument in field {self.name}')
                args_list.append(a.gql())

            gql = f'{description_str}{self.name}({", ".join(args_list)}) : {t}'
        else:
            gql = f'{description_str}{self.name} : {t}'

        if not len(self.directives):
            return gql
        else:
            if with_directives:
                return f'{gql} {" ".join([d.gql() for d in self.directives])}'
            else:
                return f'{gql}'

    def directive(self, directive_name):
        return next(filter(lambda d: d.name == directive_name, self.directives or []), None)

    def has_directive(self, directive_name):
        return self.directive(directive_name=directive_name) is not None

    @property
    def is_array(self) -> bool:
        target = get_named_type(self.type)
        if ArrayType(target).gql() == self.type.gql():
            return True
        elif ArrayType(NonNullableType(target)).gql() == self.type.gql():
            return True
        elif NonNullableType(ArrayType(target)).gql() == self.type.gql():
            return True
        return False
