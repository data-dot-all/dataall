import logging

from dataall.base.api.context import Context

from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService

log = logging.getLogger(__name__)


def create_redshift_connection(context: Context, source, input=None):
    # TODO: validate input

    admin_group = input['SamlGroupName']
    uri = input['environmentUri']
    return RedshiftConnectionService.create_redshift_connection(uri=uri, admin_group=admin_group, data=input)


def delete_redshift_connection(context: Context, source, connectionUri):
    return RedshiftConnectionService.delete_redshift_connection(uri=connectionUri)


def list_environment_redshift_connections(context: Context, source, filter):
    # At the moment this resolver is not
    environmentUri = filter['environmentUri']
    return RedshiftConnectionService.list_environment_redshift_connections(uri=environmentUri, filter=filter)
