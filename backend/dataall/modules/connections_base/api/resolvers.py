import logging

from dataall.base.api.context import Context
from dataall.base.db import exceptions

from dataall.modules.connections_base.services.connection_list_service import ConnectionListService

log = logging.getLogger(__name__)


def required_uri(uri):
    if not uri:
        raise exceptions.RequiredParameter('URI')

def list_environment_connections(context: Context, source, filter):
    uri = filter.get('environmentUri', None)
    required_uri(uri)
    return ConnectionListService.list_environment_connections(uri=uri, filter=filter)
