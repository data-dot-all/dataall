import logging

from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.vpc.services.vpc_service import VpcService

log = logging.getLogger(__name__)


def _validate_input(data):
    if not data:
        raise exceptions.RequiredParameter(data)
    if not data.get('environmentUri'):
        raise exceptions.RequiredParameter('environmentUri')
    if not data.get('SamlGroupName'):
        raise exceptions.RequiredParameter('group')
    if not data.get('label'):
        raise exceptions.RequiredParameter('label')


def create_network(context: Context, source, input):
    _validate_input(input)
    environment = EnvironmentService.get_environment_by_uri(uri=input.get('environmentUri'))
    return VpcService.create_network(
        uri=environment.environmentUri, environment=environment, admin_group=input.get('SamlGroupName'), data=input
    )


def delete_network(context: Context, source, vpcUri=None):
    if not vpcUri:
        raise exceptions.RequiredParameter('vpcUri')
    return VpcService.delete_network(uri=vpcUri)
