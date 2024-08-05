from enum import Enum


class RedshiftType(Enum):
    Serverless = 'serverless'
    Cluster = 'cluster'


class RedshiftEncryptionType(Enum):
    AWS_OWNED_KMS_KEY = 'AWS_OWNED_KMS_KEY'
    CUSTOMER_MANAGED_KMS_KEY = 'CUSTOMER_MANAGED_KMS_KEY'
    HSM = 'HSM'


class RedshiftConnectionTypes(Enum):
    DATA_USER = 'DATA_USER'
    ADMIN = 'ADMIN'
