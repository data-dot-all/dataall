from enum import Enum

from .slugify import slugify


class NamingConventionPattern(Enum):

    S3 = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    IAM = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 63}
    GLUE = {'regex': '[^a-zA-Z0-9_]', 'separator': '_', 'max_length': 63}
    GLUE_ETL = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 52}
    NOTEBOOK = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    DEFAULT = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 63}
    OPENSEARCH = {'regex': '[^a-z0-9-]', 'separator': '-', 'max_length': 27}
    OPENSEARCH_SERVERLESS = {'regex': '[^a-z0-9-]', 'separator': '-', 'max_length': 31}


class NamingConventionService:
    def __init__(
        self,
        target_label: str,
        target_uri: str,
        pattern: NamingConventionPattern,
        resource_prefix: str,
    ):
        self.target_label = target_label
        self.target_uri = target_uri if target_uri else ""
        self.service = pattern.name
        self.resource_prefix = resource_prefix

    def build_compliant_name(self) -> str:
        """
        Builds a compliant AWS resource name
        """
        regex = NamingConventionPattern[self.service].value['regex']
        separator = NamingConventionPattern[self.service].value['separator']
        max_length = NamingConventionPattern[self.service].value['max_length']
        suffix = f"-{self.target_uri}" if len(self.target_uri) else ""
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(max_length- len(self.resource_prefix + self.target_uri))] + suffix, regex_pattern=fr'{regex}', separator=separator, lowercase=True)}"
