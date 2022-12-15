from enum import Enum
from . import gql


class GraphQLEnumMapper(Enum):
    @classmethod
    def toGraphQLEnum(cls):
        return gql.GraphqlEnum(name=cls.__name__, values=cls)

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


class Context:
    def __init__(
        self,
        engine=None,
        es=None,
        username=None,
        groups=None,
        cdkproxyurl=None,
    ):
        self.engine = engine
        self.es = es
        self.username = username
        self.groups = groups
        self.cdkproxyurl = cdkproxyurl


