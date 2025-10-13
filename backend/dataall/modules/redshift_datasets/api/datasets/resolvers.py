import logging
from typing import Any
from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset, RedshiftTable
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService
from dataall.modules.redshift_datasets.services.redshift_connection_service import RedshiftConnectionService
from dataall.modules.redshift_datasets.services.redshift_constants import (
    GLOSSARY_REDSHIFT_DATASET_NAME,
    GLOSSARY_REDSHIFT_DATASET_TABLE_NAME,
)

log = logging.getLogger(__name__)


def import_redshift_dataset(context: Context, source, input=None):
    RequestValidator.validate_dataset_import_request(input)
    admin_group = input['SamlAdminGroupName']
    uri = input['environmentUri']
    return RedshiftDatasetService.import_redshift_dataset(uri=uri, admin_group=admin_group, data=input)


def update_redshift_dataset(context: Context, source, datasetUri: str, input: dict):
    RequestValidator.required_param('datasetUri', datasetUri)
    return RedshiftDatasetService.update_redshift_dataset(uri=datasetUri, data=input)


def delete_redshift_dataset(context: Context, source, datasetUri: str):
    RequestValidator.required_param('datasetUri', datasetUri)
    return RedshiftDatasetService.delete_redshift_dataset(uri=datasetUri)


def list_redshift_schema_dataset_tables(context: Context, source, datasetUri: str):
    RequestValidator.required_param('datasetUri', datasetUri)
    return RedshiftDatasetService.list_redshift_schema_dataset_tables(uri=datasetUri)


def add_redshift_dataset_tables(context: Context, source, datasetUri: str, tables: [str]):
    RequestValidator.required_param('datasetUri', datasetUri)
    RequestValidator.required_param('tables', tables)
    return RedshiftDatasetService.add_redshift_dataset_tables(uri=datasetUri, tables=tables)


def delete_redshift_dataset_table(context: Context, source, rsTableUri: str):
    RequestValidator.required_param('rsTableUri', rsTableUri)
    return RedshiftDatasetService.delete_redshift_dataset_table(uri=rsTableUri)


def update_redshift_dataset_table(context: Context, source, rsTableUri: str, input: dict):
    RequestValidator.required_param('rsTableUri', rsTableUri)
    return RedshiftDatasetService.update_redshift_dataset_table(uri=rsTableUri, data=input)


def get_redshift_dataset(context, source, datasetUri: str):
    RequestValidator.required_param('datasetUri', datasetUri)
    return RedshiftDatasetService.get_redshift_dataset(uri=datasetUri)


def list_redshift_dataset_tables(context, source, datasetUri: str, filter: dict = None):
    RequestValidator.required_param('datasetUri', datasetUri)
    return RedshiftDatasetService.list_redshift_dataset_tables(uri=datasetUri, filter=filter)


def get_redshift_dataset_table(context, source, rsTableUri: str):
    RequestValidator.required_param('rsTableUri', rsTableUri)
    return RedshiftDatasetService.get_redshift_dataset_table(uri=rsTableUri)


def list_redshift_dataset_table_columns(context, source, rsTableUri: str, filter: dict = None):
    RequestValidator.required_param('rsTableUri', rsTableUri)
    return RedshiftDatasetService.list_redshift_dataset_table_columns(uri=rsTableUri, filter=filter)


def resolve_dataset_organization(context, source: RedshiftDataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return OrganizationRepository.get_organization_by_uri(session, source.organizationUri)


def resolve_dataset_environment(
    context, source: RedshiftDataset, **kwargs
):  # TODO- duplicated with S3 datasets - follow-up PR
    if not source:
        return None
    return EnvironmentService.find_environment_by_uri(uri=source.environmentUri)


def resolve_dataset_owners_group(
    context, source: RedshiftDataset, **kwargs
):  # TODO- duplicated with S3 datasets - follow-up PR
    if not source:
        return None
    return source.SamlAdminGroupName


def resolve_dataset_stewards_group(
    context, source: RedshiftDataset, **kwargs
):  # TODO- duplicated with S3 datasets - follow-up PR
    if not source:
        return None
    return source.stewards


def resolve_user_role(
    context: Context, source: RedshiftDataset, **kwargs
):  # TODO- duplicated with S3 datasets - follow-up PR
    if not source:
        return None
    if source.owner == context.username:
        return DatasetRole.Creator.value
    elif source.SamlAdminGroupName in context.groups:
        return DatasetRole.Admin.value
    elif source.stewards in context.groups:
        return DatasetRole.DataSteward.value
    else:
        with context.engine.scoped_session() as session:
            other_modules_user_role = RedshiftDatasetService.get_other_modules_dataset_user_role(
                session, source.datasetUri, context.username, context.groups
            )
            if other_modules_user_role is not None:
                return other_modules_user_role
    return DatasetRole.NoPermission.value


def resolve_dataset_glossary_terms(context: Context, source: RedshiftDataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(session, source.datasetUri, GLOSSARY_REDSHIFT_DATASET_NAME)


def resolve_table_glossary_terms(context: Context, source: RedshiftTable, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(
            session, source.rsTableUri, GLOSSARY_REDSHIFT_DATASET_TABLE_NAME
        )


def resolve_dataset_connection(context: Context, source: RedshiftDataset, **kwargs):
    return RedshiftConnectionService.get_redshift_connection_by_uri(uri=source.connectionUri)


def resolve_dataset_upvotes(context: Context, source: RedshiftDataset, **kwargs):
    return RedshiftDatasetService.get_dataset_upvotes(uri=source.datasetUri)


def resolve_table_dataset(context: Context, source: RedshiftTable, **kwargs):
    return RedshiftDatasetService.get_redshift_dataset(uri=source.datasetUri)


class RequestValidator:
    @staticmethod
    def required_param(param_name: str, param_value: Any):
        if not param_value:
            raise exceptions.RequiredParameter(param_name)

    @staticmethod
    def validate_dataset_import_request(data):
        RequestValidator.required_param('input', data)
        RequestValidator.required_param('label', data.get('label'))
        RequestValidator.required_param('SamlAdminGroupName', data.get('SamlAdminGroupName'))
        RequestValidator.required_param('connectionUri', data.get('connectionUri'))
        RequestValidator.required_param('schema', data.get('schema'))
