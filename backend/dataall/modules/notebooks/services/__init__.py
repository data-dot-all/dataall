"""
Contains the code needed for service layer.
The service layer is a layer where all business logic is aggregated
"""

from dataall.db.api import TargetType
from dataall.modules.notebooks.services import services, permissions

__all__ = ["services", "permissions"]

TargetType("notebook", permissions.GET_NOTEBOOK, permissions.UPDATE_NOTEBOOK)
