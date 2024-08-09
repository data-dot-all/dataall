from enum import Enum
from dataall.base.api import gql


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

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def has_key(cls, key):
        return key in cls._member_map_


class SortDirection(GraphQLEnumMapper):
    asc = 'asc'
    desc = 'desc'


GLUEBUSINESSPROPERTIES = ['EXAMPLE_GLUE_PROPERTY_TO_BE_ADDED_ON_ES']
