from enum import Enum
from types import DynamicClassAttribute

from dataall.base.api import gql
from dataall.base.context import get_context


class GraphQLEnumMapper(Enum):
    @classmethod
    def toGraphQLEnum(cls):
        return gql.Enum(name=cls.__name__, values=cls)

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

    # temporary hack to return enum names when request comes from AppSync and enum values when request comes from APIGW
    @DynamicClassAttribute
    def value(self):
        try:
            if get_context().is_appsync:
                return self.name
            else:
                return super().value
        except AttributeError:
            return super().value


class SortDirection(GraphQLEnumMapper):
    asc = 'asc'
    desc = 'desc'


GLUEBUSINESSPROPERTIES = ['EXAMPLE_GLUE_PROPERTY_TO_BE_ADDED_ON_ES']
