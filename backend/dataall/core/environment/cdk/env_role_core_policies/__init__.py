"""Contains the code for creating environment policies"""

from dataall.core.environment.cdk.env_role_core_policies import (
    cloudformation,
    data_policy,
    service_policy,
    athena,
    secretsmanager,
    sqs,
    ssm,
)

__all__ = ['cloudformation', 'data_policy', 'service_policy', 'athena', 'secretsmanager', 'sqs', 'ssm']
