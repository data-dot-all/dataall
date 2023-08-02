"""
This package contains modules that are used to create a CloudFormation stack in AWS.
The code is invoked in ECS Fargate to initialize the creation of the stack
"""
from dataall.modules.notebooks.cdk import notebook_stack, notebook_policy, pivot_role_notebooks_policy

__all__ = ["notebook_stack", "notebook_policy", "pivot_role_notebooks_policy"]
