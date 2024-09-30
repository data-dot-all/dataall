import logging
import re
from typing import Any
from dataall.base.db import exceptions
from dataall.base.api.context import Context

from dataall.modules.redshift_datasets.api.connections.enums import RedshiftType
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService

log = logging.getLogger(__name__)


def create_redshift_connection(context: Context, source, input=None):
    RequestValidator.validate_connection_creation_request(data=input)
    return RedshiftConnectionService.create_redshift_connection(
        uri=input['environmentUri'], admin_group=input['SamlGroupName'], data=input
    )


def delete_redshift_connection(context: Context, source, connectionUri: str):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.delete_redshift_connection(uri=connectionUri)


def list_environment_redshift_connections(context: Context, source, filter: dict = None):
    environmentUri = filter['environmentUri']
    RequestValidator.validate_uri('environmentUri', environmentUri)
    return RedshiftConnectionService.list_environment_redshift_connections(uri=environmentUri, filter=filter)


def list_redshift_connection_schemas(context: Context, source, connectionUri):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.list_connection_schemas(uri=connectionUri)


def list_redshift_schema_tables(context: Context, source, connectionUri: str, schema: str):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.list_schema_tables(uri=connectionUri, schema=schema)


def add_redshift_connection_group_permissions(
    context: Context, source, connectionUri: str, groupUri: str, permissions: list
):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.add_group_permissions(uri=connectionUri, group=groupUri, permissions=permissions)


def delete_redshift_connection_group_permissions(context: Context, source, connectionUri: str, groupUri: str):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.delete_group_permissions(uri=connectionUri, group=groupUri)


def list_redshift_connection_group_permissions(context: Context, source, connectionUri: str, filter: dict = None):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.list_connection_group_permissions(uri=connectionUri, filter=filter)


def list_redshift_connection_group_no_permissions(context: Context, source, connectionUri: str, filter: dict = None):
    RequestValidator.validate_uri('connectionUri', connectionUri)
    return RedshiftConnectionService.list_connection_group_no_permissions(uri=connectionUri, filter=filter)


class RequestValidator:
    @staticmethod
    def _required_param(param_name: str, param_value: Any):
        if not param_value:
            raise exceptions.RequiredParameter(param_name)

    @staticmethod
    def validate_uri(param_name: str, param_value: str):
        RequestValidator._required_param(param_name, param_value)
        pattern = r'^[a-z0-9]{8}$'
        if not re.match(pattern, param_value):
            raise exceptions.InvalidInput(
                param_name=param_name,
                param_value=param_value,
                constraint='8 characters long and contain only lowercase letters and numbers',
            )

    @staticmethod
    def validate_connection_creation_request(data):
        if not data:
            raise exceptions.RequiredParameter('data')

        RequestValidator.validate_uri('environmentUri', data.get('environmentUri'))
        RequestValidator._required_param('SamlGroupName', data.get('SamlGroupName'))
        RequestValidator._required_param('connectionName', data.get('connectionName'))
        RequestValidator._required_param('redshiftType', data.get('redshiftType'))
        if data.get('redshiftType') not in [RedshiftType.Serverless.value, RedshiftType.Cluster.value]:
            raise exceptions.InvalidInput('redshiftType', data.get('redshiftType'), 'Serverless or Cluster')
        RequestValidator._required_param('database', data.get('database'))
        if not data.get('redshiftUser') and not data.get('secretArn'):
            raise exceptions.RequiredParameter('RedshiftUser OR secretArn')
        if data.get('redshiftType') == RedshiftType.Serverless.value:
            RequestValidator._required_param('nameSpaceId', data.get('nameSpaceId'))
            RequestValidator._required_param('workgroup', data.get('workgroup'))
            pattern = '^[a-z0-9-]*$'
            if not re.match(pattern, data.get('workgroup')):
                raise exceptions.InvalidInput(
                    param_name='workgroup',
                    param_value=data.get('workgroup'),
                    constraint='contain only lowercase letters and numbers',
                )
        if data.get('redshiftType') == RedshiftType.Cluster.value:
            RequestValidator._required_param('clusterId', data.get('clusterId'))
