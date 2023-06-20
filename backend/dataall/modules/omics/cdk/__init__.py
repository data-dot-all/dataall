"""
This package contains modules that are used to create a CloudFormation stack in AWS.
The code is invoked in ECS Fargate to initialize the creation of the stack
"""
from dataall.modules.notebooks.cdk import stacks
from dataall.modules.notebooks.cdk import policies

__all__ = ["omics_stack.py", "omics_policy.py"]
