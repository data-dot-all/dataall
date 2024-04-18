from dataall.base.api.context import Context
from dataall.core.stacks.api import stack_helper
from dataall.base.db import exceptions
from dataall.modules.maintenance.api.enums import MaintenanceModes
from dataall.modules.maintenance.api.types import Maintenance
from dataall.modules.maintenance.services.maintenance_service import MaintenanceService
from dataall.modules.notebooks.api.enums import SagemakerNotebookRole
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.modules.notebooks.services.notebook_service import NotebookService, NotebookCreationRequest


def create_notebook(context: Context, source: SagemakerNotebook, input: dict = None):
    """Creates a SageMaker notebook. Deploys the notebooks stack into AWS"""
    RequestValidator.validate_creation_request(input)
    request = NotebookCreationRequest.from_dict(input)
    return NotebookService.create_notebook(
        uri=input['environmentUri'], admin_group=input['SamlAdminGroupName'], request=request
    )


def start_maintenance_window(context: Context, source: Maintenance, mode: str):
    """Starts the maintenance window"""
    if mode not in [item.value for item in list(MaintenanceModes)]:
        raise Exception('Mode is not conforming to the MaintenanceModes enums')
    # Check from the context if the groups contains the DataAdminstrators group
    return MaintenanceService.start_maintenance_window(mode=mode)


def stop_maintenance_window(context: Context, source: Maintenance):
    # Check from the context if the groups contains the DataAdminstrators group
    return MaintenanceService.stop_maintenance_window()

def get_maintenance_window_status(context: Context, source: Maintenance):
    return MaintenanceService.get_maintenance_window_status(engine=context.engine)

def get_maintenance_window_mode(context: Context, source: Maintenance):
    return MaintenanceService.get_maintenance_window_mode()


class RequestValidator:
    """Aggregates all validation logic for operating with notebooks"""

    @staticmethod
    def required_uri(uri):
        if not uri:
            raise exceptions.RequiredParameter('URI')

    @staticmethod
    def validate_creation_request(data):
        required = RequestValidator._required
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

        required(data, 'environmentUri')
        required(data, 'SamlAdminGroupName')

    @staticmethod
    def _required(data: dict, name: str):
        if not data.get(name):
            raise exceptions.RequiredParameter(name)
