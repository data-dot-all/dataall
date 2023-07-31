"""Contains the code for creating environment policies"""

from dataall.base.cdkproxy.stacks.policies import (
    cloudformation, data_policy, service_policy, athena, secretsmanager, sqs, ssm
)

__all__ = ["cloudformation", "data_policy", "service_policy", "athena", "secretsmanager", "sqs", "ssm"]
