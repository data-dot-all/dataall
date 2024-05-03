import logging

from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.datasets.api.dataset.resolvers import get_dataset
from dataall.base.api.context import Context
from dataall.modules.datasets.services.dataset_table_service import DatasetTableService
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset

log = logging.getLogger(__name__)


def get_table(context, source: Dataset, tableUri: str = None):
    return DatasetTableService.get_table(uri=tableUri)


def update_table(context, source, tableUri: str = None, input: dict = None):
    return DatasetTableService.update_table(uri=tableUri, table_data=input)


def delete_table(context, source, tableUri: str = None):
    if not tableUri:
        return False
    return DatasetTableService.delete_table(uri=tableUri)


@is_feature_enabled('modules.datasets.features.preview_data')
def preview(context, source, tableUri: str = None):
    if not tableUri:
        return None
    return DatasetTableService.preview(table_uri=tableUri)


def get_glue_table_properties(context: Context, source: DatasetTable, **kwargs):
    if not source:
        return None
    return DatasetTableService.get_glue_table_properties(uri=source.tableUri)


def sync_tables(context: Context, source, datasetUri: str = None):
    return DatasetTableService.sync_tables_for_dataset(uri=datasetUri)


def resolve_dataset(context, source: DatasetTable, **kwargs):
    if not source:
        return None

    dataset_with_role = get_dataset(context, source=None, datasetUri=source.datasetUri)
    if not dataset_with_role:
        return None
    return dataset_with_role


def resolve_glossary_terms(context: Context, source: DatasetTable, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(session, source.tableUri, 'DatasetTable')
