import logging
from typing import List

from sqlalchemy.sql import and_

from .. import models, api, permissions, exceptions, paginate
from . import has_tenant_perm, has_resource_perm, Glossary
from ..models import Dataset
from ...utils import json_utils

logger = logging.getLogger(__name__)


class DatasetTable:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.CREATE_DATASET_TABLE)
    def create_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DatasetTable:
        dataset = api.Dataset.get_dataset_by_uri(session, uri)
        exists = (
            session.query(models.DatasetTable)
            .filter(
                and_(
                    models.DatasetTable.datasetUri == uri,
                    models.DatasetTable.GlueTableName == data['name'],
                )
            )
            .count()
        )

        if exists:
            raise exceptions.ResourceAlreadyExists(
                action='Create Table',
                message=f'table: {data["name"]} already exist on dataset {uri}',
            )

        table = models.DatasetTable(
            datasetUri=uri,
            label=data['name'],
            name=data['name'],
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            S3BucketName=dataset.S3BucketName,
            S3Prefix=data.get('S3Prefix', 'unknown'),
            AWSAccountId=dataset.AwsAccountId,
            GlueDatabaseName=dataset.GlueDatabaseName,
            GlueTableConfig=data.get('config'),
            GlueTableName=data['name'],
            owner=dataset.owner,
            region=dataset.region,
        )
        session.add(table)
        if data.get('terms') is not None:
            Glossary.set_glossary_terms_links(
                session, username, table.tableUri, 'DatasetTable', data.get('terms', [])
            )
        session.commit()
        return table

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    # @has_resource_perm(permissions.LIST_DATASET_TABLES)
    def list_dataset_tables(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> dict:
        query = (
            session.query(models.DatasetTable)
            .filter(models.DatasetTable.datasetUri == uri)
            .order_by(models.DatasetTable.created.desc())
        )
        if data.get('term'):
            term = data.get('term')
            query = query.filter(models.DatasetTable.label.ilike('%' + term + '%'))
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    # @has_resource_perm(permissions.LIST_DATASET_TABLES)
    def get_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DatasetTable:
        return DatasetTable.get_dataset_table_by_uri(session, data['tableUri'])

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.UPDATE_DATASET_TABLE)
    def update_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        table = data.get(
            'table',
            DatasetTable.get_dataset_table_by_uri(session, data['tableUri']),
        )

        for k in [attr for attr in data.keys() if attr != 'term']:
            setattr(table, k, data.get(k))

        if data.get('terms') is not None:
            Glossary.set_glossary_terms_links(
                session, username, table.tableUri, 'DatasetTable', data.get('terms', [])
            )

        return table

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.DELETE_DATASET_TABLE)
    def delete_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        table = DatasetTable.get_dataset_table_by_uri(session, data['tableUri'])
        share_item = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == table.tableUri,
                    models.ShareObjectItem.status == 'Approved',
                )
            )
            .first()
        )
        if share_item:
            raise exceptions.ResourceShared(
                action=permissions.DELETE_DATASET_TABLE,
                message='Revoke all table shares before deletion',
            )
        session.query(models.ShareObjectItem).filter(
            models.ShareObjectItem.itemUri == table.tableUri,
        ).delete()
        session.delete(table)
        Glossary.delete_glossary_terms_links(
            session, target_uri=table.tableUri, target_type='DatasetTable'
        )
        return True

    @staticmethod
    def query_dataset_tables_shared_with_env(
        session, environment_uri: str, dataset_uri: str, status: List[str]
    ):
        """For a given dataset, returns the list of Tables shared with the environment
        This means looking at approved ShareObject items
        for the share object associating the dataset and environment
        """
        env_tables_shared = (
            session.query(models.DatasetTable)  # all tables
            .join(
                models.ShareObjectItem,  # found in ShareObjectItem
                models.ShareObjectItem.itemUri == models.DatasetTable.tableUri,
            )
            .join(
                models.ShareObject,  # jump to share object
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    models.ShareObject.datasetUri == dataset_uri,  # for this dataset
                    models.ShareObject.environmentUri
                    == environment_uri,  # for this environment
                    models.ShareObject.status.in_(status),
                )
            )
            .all()
        )

        return env_tables_shared

    @staticmethod
    def get_dataset_tables_shared_with_env(
        session, environment_uri: str, dataset_uri: str, status: List[str]
    ):
        return [
            {"tableUri": t.tableUri, "GlueTableName": t.GlueTableName}
            for t in DatasetTable.query_dataset_tables_shared_with_env(
                session, environment_uri, dataset_uri, status
            )
        ]

    @staticmethod
    def get_dataset_table_by_uri(session, table_uri):
        table: models.DatasetTable = session.query(models.DatasetTable).get(table_uri)
        if not table:
            raise exceptions.ObjectNotFound('DatasetTable', table_uri)
        return table

    @staticmethod
    def sync(session, datasetUri, glue_tables=None):

        dataset: Dataset = session.query(Dataset).get(datasetUri)
        if dataset:
            existing_tables = (
                session.query(models.DatasetTable)
                .filter(models.DatasetTable.datasetUri == datasetUri)
                .all()
            )
            existing_table_names = [e.GlueTableName for e in existing_tables]
            existing_dataset_tables_map = {t.GlueTableName: t for t in existing_tables}

            DatasetTable.update_existing_tables_status(existing_tables, glue_tables)

            for table in glue_tables:
                if table['Name'] not in existing_table_names:
                    logger.info(
                        f'Storing new table: {table} for dataset db {dataset.GlueDatabaseName}'
                    )
                    updated_table = models.DatasetTable(
                        datasetUri=dataset.datasetUri,
                        label=table['Name'],
                        name=table['Name'],
                        region=dataset.region,
                        owner=dataset.owner,
                        GlueDatabaseName=dataset.GlueDatabaseName,
                        AWSAccountId=dataset.AwsAccountId,
                        S3BucketName=dataset.S3BucketName,
                        S3Prefix=table.get('StorageDescriptor', {}).get('Location'),
                        GlueTableName=table['Name'],
                        LastGlueTableStatus='InSync',
                        GlueTableProperties=json_utils.to_json(
                            table.get('Parameters', {})
                        ),
                    )
                    session.add(updated_table)
                    session.commit()
                else:
                    logger.info(
                        f'Updating table: {table} for dataset db {dataset.GlueDatabaseName}'
                    )
                    updated_table: models.DatasetTable = (
                        existing_dataset_tables_map.get(table['Name'])
                    )
                    updated_table.GlueTableProperties = json_utils.to_json(
                        table.get('Parameters', {})
                    )

                DatasetTable.sync_table_columns(session, updated_table, table)

        return True

    @staticmethod
    def update_existing_tables_status(existing_tables, glue_tables):
        for existing_table in existing_tables:
            if existing_table.GlueTableName not in [t['Name'] for t in glue_tables]:
                existing_table.LastGlueTableStatus = 'Deleted'
                logger.info(
                    f'Table {existing_table.GlueTableName} status set to Deleted from Glue.'
                )

    @staticmethod
    def sync_table_columns(session, dataset_table, glue_table):

        DatasetTable.delete_all_table_columns(session, dataset_table)

        columns = [
            {**item, **{'columnType': 'column'}}
            for item in glue_table.get('StorageDescriptor', {}).get('Columns', [])
        ]
        partitions = [
            {**item, **{'columnType': f'partition_{index}'}}
            for index, item in enumerate(glue_table.get('PartitionKeys', []))
        ]

        logger.debug(f'Found columns {columns} for table {dataset_table}')
        logger.debug(f'Found partitions {partitions} for table {dataset_table}')

        for col in columns + partitions:
            table_col = models.DatasetTableColumn(
                name=col['Name'],
                description=col.get('Comment', 'No description provided'),
                label=col['Name'],
                owner=dataset_table.owner,
                datasetUri=dataset_table.datasetUri,
                tableUri=dataset_table.tableUri,
                AWSAccountId=dataset_table.AWSAccountId,
                GlueDatabaseName=dataset_table.GlueDatabaseName,
                GlueTableName=dataset_table.GlueTableName,
                region=dataset_table.region,
                typeName=col['Type'],
                columnType=col['columnType'],
            )
            session.add(table_col)

    @staticmethod
    def delete_all_table_columns(session, dataset_table):
        session.query(models.DatasetTableColumn).filter(
            and_(
                models.DatasetTableColumn.GlueDatabaseName
                == dataset_table.GlueDatabaseName,
                models.DatasetTableColumn.GlueTableName == dataset_table.GlueTableName,
            )
        ).delete()
        session.commit()

    @staticmethod
    def get_dataset_by_uri(session, table_uri):
        table: models.DatasetTable = session.query(models.DatasetTable).get(table_uri)
        if not table:
            raise Exception(f'DatasetTableNotFound{table_uri}')
        dataset: Dataset = session.query(Dataset).get(table.datasetUri)
        if not dataset:
            raise Exception(f'DatasetNotFound{table.datasetUri}')
        return dataset

    @staticmethod
    def list_all_tables(session) -> models.DatasetTable:
        tables = session.query(models.DatasetTable).all()
        logging.info(f'All Tables found {tables}')
        return tables

    @staticmethod
    def get_table_by_s3_prefix(session, s3_prefix, accountid, region):
        table: models.DatasetTable = (
            session.query(models.DatasetTable)
            .filter(
                and_(
                    models.DatasetTable.S3Prefix.startswith(s3_prefix),
                    models.DatasetTable.AWSAccountId == accountid,
                    models.DatasetTable.region == region,
                )
            )
            .first()
        )
        if not table:
            logging.info(f'No table found for  {s3_prefix}|{accountid}|{region}')
        else:
            logging.info(
                f'Found table {table.tableUri}|{table.GlueTableName}|{table.S3Prefix}'
            )
            return table
