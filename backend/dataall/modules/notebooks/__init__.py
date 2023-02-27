"""Contains the code related to SageMaker notebooks"""
from dataall.db.api import TargetType
from dataall.modules.notebooks import gql, models, cdk, services, permissions

# importing of the common code
import dataall.modules.common.sagemaker as common

__all__ = ["gql", "models", "cdk", "services", "permissions", "common"]

TargetType("notebook", permissions.GET_NOTEBOOK, permissions.UPDATE_NOTEBOOK)
