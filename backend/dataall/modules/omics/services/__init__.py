"""
Contains the code needed for service layer.
The service layer is a layer where all business logic is aggregated
"""

from dataall.modules.omics.services import omics_service, omics_permissions

__all__ = ['omics_service', 'omics_permissions']
