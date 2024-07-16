import logging
from typing import Any
from dataall.base.db import exceptions
from dataall.base.api.context import Context

from dataall.modules.redshift_datasets.api.connections.enums import RedshiftType
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService

log = logging.getLogger(__name__)


def create_redshift_connection(context: Context, source, input=None):
    _validate_creation_request(data=input)
    return RedshiftConnectionService.create_redshift_connection(
        uri=input['environmentUri'], admin_group=input['SamlGroupName'], data=input
    )

def delete_redshift_connection(context: Context, source, connectionUri: str):
    _required_param('connectionUri', connectionUri)
    return RedshiftConnectionService.delete_redshift_connection(uri=connectionUri)


def list_environment_redshift_connections(context: Context, source, filter: dict = None):
    environmentUri = filter['environmentUri']
    _required_param('environmentUri', environmentUri)
    return RedshiftConnectionService.list_environment_redshift_connections(uri=environmentUri, filter=filter)


def list_redshift_connection_schemas(context: Context, source, connectionUri):
    _required_param('connectionUri', connectionUri)
    return RedshiftConnectionService.list_connection_schemas(uri=connectionUri)


def list_redshift_schema_tables(context: Context, source, connectionUri: str, schema: str):
    _required_param('connectionUri', connectionUri)
    _required_param('schema', schema)
    return RedshiftConnectionService.list_schema_tables(uri=connectionUri, schema=schema)


def _required_param(param_name: str, param_value: Any):
    if not param_value:
        raise exceptions.RequiredParameter(param_name)


def _validate_creation_request(data):
    if not data:
        raise exceptions.RequiredParameter('data')

    _required_param('SamlGroupName', data.get('SamlGroupName'))
    _required_param('environmentUri', data.get('environmentUri'))
    _required_param('connectionName', data.get('connectionName'))
    _required_param('redshiftType', data.get('redshiftType'))
    _required_param('database', data.get('database'))
    if not data.get('redshiftUser') and not data.get('secretArn'):
        raise exceptions.RequiredParameter('RedshiftUser OR secretArn')
    if data.get('redshiftType') == RedshiftType.Serverless.value:
        _required_param('nameSpaceId', data.get('nameSpaceId'))
        _required_param('workgroup', data.get('workgroup'))
    if data.get('redshiftType') == RedshiftType.Cluster.value:
        _required_param('clusterId', data.get('clusterId'))
