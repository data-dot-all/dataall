"""
This package contains modules that are used to create a CloudFormation stack in AWS.
The code is invoked in ECS Fargate to initialize the creation of the stack
"""

from dataall.modules.omics.cdk import omics_policy

__all__ = ["omics_policy"]
