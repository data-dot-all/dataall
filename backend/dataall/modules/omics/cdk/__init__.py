"""
This package contains modules that are used to create a CloudFormation stack in AWS.
The code is invoked in ECS Fargate to initialize the creation of the stack
"""

from dataall.modules.omics.cdk import pivot_role_omics_policy, env_role_omics_policy

__all__ = ['pivot_role_omics_policy', 'env_role_omics_policy']
