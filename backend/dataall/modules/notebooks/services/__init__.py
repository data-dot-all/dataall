"""Contains the code needed for service layer"""

from dataall.db.api import TargetType
from dataall.modules.notebooks.services import services, permissions
from dataall.modules.common.sagemaker import permissions as common_permission

__all__ = ["services", "permissions", "common_permission"]

TargetType("notebook", permissions.GET_NOTEBOOK, permissions.UPDATE_NOTEBOOK)
