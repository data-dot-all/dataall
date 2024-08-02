from dataall.base.api.constants import GraphQLEnumMapper
from dataall.base.config import config
from dataall.base.db.exceptions import InvalidInput

custom_confidentiality_mapping = config.get_property('modules.s3_datasets.features.custom_confidentiality_mapping', {})


class DatasetTypes(GraphQLEnumMapper):
    S3 = 'S3'
    Redshift = 'Redshift'


class DatasetRole(GraphQLEnumMapper):
    # Permissions on a dataset
    BusinessOwner = '999'
    DataSteward = '998'
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


class DatasetSortField(GraphQLEnumMapper):
    label = 'label'
    created = 'created'
    updated = 'updated'


class ConfidentialityClassification(GraphQLEnumMapper):
    Unclassified = 'Unclassified'
    Official = 'Official'
    Secret = 'Secret'

    @staticmethod
    def get_confidentiality_level(confidentiality):
        return (
            confidentiality
            if not custom_confidentiality_mapping
            else custom_confidentiality_mapping.get(confidentiality, None)
        )

    @staticmethod
    def validate_confidentiality_level(confidentiality):
        if config.get_property('modules.datasets_base.features.confidentiality_dropdown', False):
            confidentiality = ConfidentialityClassification.get_confidentiality_level(confidentiality)
            if confidentiality not in [item.value for item in list(ConfidentialityClassification)]:
                raise InvalidInput(
                    'Confidentiality Name',
                    confidentiality,
                    'does not conform to the confidentiality classification. Hint: Check your confidentiality value OR check your mapping if you are using custom confidentiality values',
                )
        return True


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
