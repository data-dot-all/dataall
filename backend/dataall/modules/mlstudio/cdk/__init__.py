"""
This package contains modules that are used to create a CloudFormation stack in AWS.
The code is invoked in ECS Fargate to initialize the creation of the stack
"""

from dataall.modules.mlstudio.cdk import (
    mlstudio_stack,
    env_role_mlstudio_policy,
    pivot_role_mlstudio_policy,
    mlstudio_extension,
)

__all__ = ['mlstudio_stack', 'env_role_mlstudio_policy', 'pivot_role_mlstudio_policy', 'mlstudio_extension']
