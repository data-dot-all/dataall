"""
Contains the code needed for service layer.
The service layer is a layer where all business logic is aggregated
"""

from dataall.modules.notebooks.services import notebook_service, notebook_permissions

__all__ = ['notebook_service', 'notebook_permissions']
