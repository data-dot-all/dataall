"""Contains the code for creating pivot role policies"""

from dataall.core.environment.cdk.pivot_role_core_policies import (
    cloudformation,
    iam,
    kms,
    logging,
    s3,
    sns,
    sqs,
    ssm,
    sts
)

__all__ = [
    "cloudformation",
    "iam",
    "kms",
    "logging",
    "s3",
    "sns",
    "sqs",
    "ssm",
    "sts"
]
