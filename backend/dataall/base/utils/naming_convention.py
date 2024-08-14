from enum import Enum
import re
from .slugify import slugify


class NamingConventionPattern(Enum):
    S3 = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    IAM = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 63}  # Role names up to 64 chars
    IAM_POLICY = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 128}  # Policy names up to 128 chars
    GLUE = {'regex': '[^a-zA-Z0-9_]', 'separator': '_', 'max_length': 240}  # Limit 255 - 15 extra chars buffer
    GLUE_ETL = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 52}
    NOTEBOOK = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    MLSTUDIO_DOMAIN = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    DEFAULT = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 63}
    OPENSEARCH = {'regex': '[^a-z0-9-]', 'separator': '-', 'max_length': 27}
    OPENSEARCH_SERVERLESS = {'regex': '[^a-z0-9-]', 'separator': '-', 'max_length': 31}
    DATA_FILTERS = {'regex': '^[a-z0-9_]*$', 'separator': '_', 'max_length': 31}
    REDSHIFT_DATASHARE = {
        'regex': '[^a-zA-Z0-9_]',
        'separator': '_',
        'max_length': 1000,
    }  # Maximum length of 2147483647


class NamingConventionService:
    def __init__(
        self,
        target_label: str,
        pattern: NamingConventionPattern,
        target_uri: str = '',
        resource_prefix: str = '',
    ):
        self.target_label = target_label
        self.target_uri = target_uri if target_uri else ''
        self.service = pattern.name
        self.resource_prefix = resource_prefix

    def build_compliant_name(self) -> str:
        """
        Builds a compliant AWS resource name
        """
        regex = NamingConventionPattern[self.service].value['regex']
        separator = NamingConventionPattern[self.service].value['separator']
        max_length = NamingConventionPattern[self.service].value['max_length']
        suffix = f'-{self.target_uri}' if len(self.target_uri) else ''
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(max_length- len(self.resource_prefix + self.target_uri))] + suffix, regex_pattern=fr'{regex}', separator=separator, lowercase=True)}"

    def validate_name(self):
        regex = NamingConventionPattern[self.service].value['regex']
        max_length = NamingConventionPattern[self.service].value['max_length']
        if not re.search(regex, self.target_label):
            raise Exception(
                f'An error occurred (InvalidInput): label value {self.target_label} must match the pattern {regex}'
            )
        elif len(self.target_label) > max_length:
            raise Exception(
                f'An error occurred (InvalidInput): label value {self.target_label} must be less than {max_length} characters'
            )
