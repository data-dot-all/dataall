from dataall.base.api.constants import GraphQLEnumMapper


class DatasetRole(GraphQLEnumMapper):
    # Permissions on a dataset
    BusinessOwner = '999'
    DataSteward = '998'
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class ConfidentialityClassification(GraphQLEnumMapper):
    Unclassified = 'Unclassified'
    Official = 'Official'
    Secret = 'Secret'


class DatasetSortField(GraphQLEnumMapper):
    label = 'label'
    created = 'created'
    updated = 'updated'


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

