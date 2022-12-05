from enum import Enum

from .slugify import slugify


class NamingConventionPattern(Enum):
    def __str__(self):
        return self.value

    S3 = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    IAM = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 63}
    GLUE = {'regex': '[^a-zA-Z0-9_]', 'separator': '_', 'max_length': 63}
    NOTEBOOK = {'regex': '[^a-zA-Z0-9-]', 'separator': '-', 'max_length': 63}
    DEFAULT = {'regex': '[^a-zA-Z0-9-_]', 'separator': '-', 'max_length': 63}


class NamingConventionService:
    def __init__(
        self,
        target_label: str,
        target_uri: str,
        pattern: NamingConventionPattern,
        resource_prefix: str,
    ):
        self.target_label = target_label
        self.target_uri = target_uri
        self.service = pattern
        self.resource_prefix = resource_prefix

    def build_compliant_name(self) -> str:
        """
        Builds a compliant AWS resource name
        """
        if self.service == NamingConventionPattern.S3:
            regex = self.service.S3.value['regex']
            return self.build_s3_compliant_name(regex)
        elif self.service == NamingConventionPattern.IAM:
            regex = self.service.IAM.value['regex']
            return self.build_iam_compliant_name(regex)
        elif self.service == NamingConventionPattern.GLUE:
            regex = self.service.GLUE.value['regex']
            return self.build_glue_compliant_name(regex)
        elif self.service == NamingConventionPattern.NOTEBOOK:
            regex = self.service.NOTEBOOK.value['regex']
            return self.build_notebook_compliant_name(regex)
        else:
            regex = self.service.DEFAULT.value['regex']
            return self.build_default_compliant_name(regex)

    def build_s3_compliant_name(self, regex) -> str:
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(self.service.S3.value['max_length'] - len(self.resource_prefix + self.target_uri))] + '-' + self.target_uri, regex_pattern=fr'{regex}', separator=self.service.S3.value['separator'], lowercase=True)}"

    def build_iam_compliant_name(self, regex) -> str:
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(self.service.IAM.value['max_length'] - len(self.resource_prefix + self.target_uri))] + '-' + self.target_uri, regex_pattern=fr'{regex}', separator=self.service.IAM.value['separator'], lowercase=True)}"

    def build_glue_compliant_name(self, regex) -> str:
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(self.service.GLUE.value['max_length'] - len(self.resource_prefix + self.target_uri))] + '-' + self.target_uri, regex_pattern=fr'{regex}', separator=self.service.GLUE.value['separator'], lowercase=True)}"

    def build_notebook_compliant_name(self, regex) -> str:
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(self.service.NOTEBOOK.value['max_length'] - len(self.resource_prefix +self.target_uri))] + '-' + self.target_uri, regex_pattern=fr'{regex}', separator=self.service.NOTEBOOK.value['separator'], lowercase=True)}"

    def build_default_compliant_name(self, regex) -> str:
        return f"{slugify(self.resource_prefix + '-' + self.target_label[:(self.service.DEFAULT.value['max_length'] - len(self.resource_prefix +self.target_uri))] + '-' + self.target_uri, regex_pattern=fr'{regex}', separator=self.service.DEFAULT.value['separator'], lowercase=True)}"
