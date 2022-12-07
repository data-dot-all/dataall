from enum import Enum
from common.api import gql


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

