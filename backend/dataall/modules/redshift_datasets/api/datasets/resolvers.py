import logging

from dataall.base.api.context import Context

from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService

log = logging.getLogger(__name__)


def import_redshift_dataset(context: Context, source, input=None):
    # TODO: validate input

    admin_group = input['SamlAdminGroupName']
    uri = input['environmentUri']
    return RedshiftDatasetService.import_redshift_dataset(uri=uri, admin_group=admin_group, data=input)
