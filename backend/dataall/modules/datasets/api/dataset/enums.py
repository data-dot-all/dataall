from dataall.api.constants import GraphQLEnumMapper


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
