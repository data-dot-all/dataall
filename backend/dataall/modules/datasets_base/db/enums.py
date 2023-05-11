from enum import Enum


class ConfidentialityClassification(Enum):
    Unclassified = 'Unclassified'
    Official = 'Official'
    Secret = 'Secret'


class DatasetRole(Enum):
    # Permissions on a dataset
    BusinessOwner = '999'
    DataSteward = '998'
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'

