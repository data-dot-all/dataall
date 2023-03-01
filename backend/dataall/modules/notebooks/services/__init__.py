"""Contains the code needed for service layer"""

from dataall.db.api import TargetType
from dataall.modules.notebooks.services import services, permissions

__all__ = ["services", "permissions"]

TargetType("notebook", permissions.GET_NOTEBOOK, permissions.UPDATE_NOTEBOOK)
