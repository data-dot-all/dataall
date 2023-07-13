"""
    1) i created it								DatasetCreator
    2) i belong to the Dataset Admin group		DatasetAdmin
    3) i'm the busoness owner					DatasetBusinessOwner
    4) i'm a steward 							DatasetSteward
    5) it's shared with one of My Env			Shared
    6) no permission at all						NoPermission
"""


from enum import Enum
from ..base.api import gql


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

class SortDirection(GraphQLEnumMapper):
    asc = 'asc'
    desc = 'desc'


class PrincipalType(GraphQLEnumMapper):
    Any = 'Any'
    Organization = 'Organization'
    Environment = 'Environment'
    User = 'User'
    Project = 'Project'
    Public = 'Public'
    Group = 'Group'
    ConsumptionRole = 'ConsumptionRole'


class Language(GraphQLEnumMapper):
    English = 'English'
    French = 'French'
    German = 'German'


class Topic(GraphQLEnumMapper):
    Finances = 'Finances'
    HumanResources = 'HumanResources'
    Products = 'Products'
    Services = 'Services'
    Operations = 'Operations'
    Research = 'Research'
    Sales = 'Sales'
    Orders = 'Orders'
    Sites = 'Sites'
    Energy = 'Energy'
    Customers = 'Customers'
    Misc = 'Misc'


GLUEBUSINESSPROPERTIES = ['EXAMPLE_GLUE_PROPERTY_TO_BE_ADDED_ON_ES']
