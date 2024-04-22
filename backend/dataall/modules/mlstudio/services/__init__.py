"""
Contains the code needed for service layer.
The service layer is a layer where all business logic is aggregated
"""

from dataall.modules.mlstudio.services import mlstudio_service, mlstudio_permissions

__all__ = ['mlstudio_service', 'mlstudio_permissions']
