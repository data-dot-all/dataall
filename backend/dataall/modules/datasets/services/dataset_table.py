import logging

from sqlalchemy.sql import and_

from dataall.db import models, api, permissions, exceptions, paginate
from dataall.db.api import has_tenant_perm, has_resource_perm, Glossary, ResourcePolicy, Environment
from dataall.modules.datasets.services.permissions import MANAGE_DATASETS
from dataall.modules.datasets.services.dataset_service import DatasetService
from dataall.utils import json_utils
from dataall.modules.datasets.db.models import DatasetTableColumn, DatasetTable, Dataset

logger = logging.getLogger(__name__)


class DatasetTableService:
    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(permissions.CREATE_DATASET_TABLE)
    def create_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> DatasetTable:
        dataset = DatasetService.get_dataset_by_uri(session, uri)
        exists = (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.datasetUri == uri,
                    DatasetTable.GlueTableName == data['name'],
                )
            )
            .count()
        )

        if exists:
            raise exceptions.ResourceAlreadyExists(
                action='Create Table',
                message=f'table: {data["name"]} already exist on dataset {uri}',
            )

        table = DatasetTable(
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

        # ADD DATASET TABLE PERMISSIONS
        environment = Environment.get_environment_by_uri(session, dataset.environmentUri)
        permission_group = set([dataset.SamlAdminGroupName, environment.SamlGroupName, dataset.stewards if dataset.stewards is not None else dataset.SamlAdminGroupName])
        for group in permission_group:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=group,
                permissions=permissions.DATASET_TABLE_READ,
                resource_uri=table.tableUri,
                resource_type=DatasetTable.__name__,
            )
        return table

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    def list_dataset_tables(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> dict:
        query = (
            session.query(DatasetTable)
            .filter(DatasetTable.datasetUri == uri)
            .order_by(DatasetTable.created.desc())
        )
        if data.get('term'):
            term = data.get('term')
            query = query.filter(DatasetTable.label.ilike('%' + term + '%'))
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    def get_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> DatasetTable:
        return DatasetTableService.get_dataset_table_by_uri(session, data['tableUri'])

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
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
            DatasetTableService.get_dataset_table_by_uri(session, data['tableUri']),
        )

        for k in [attr for attr in data.keys() if attr != 'term']:
            setattr(table, k, data.get(k))

        if data.get('terms') is not None:
            Glossary.set_glossary_terms_links(
                session, username, table.tableUri, 'DatasetTable', data.get('terms', [])
            )

        return table

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(permissions.DELETE_DATASET_TABLE)
    def delete_dataset_table(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        table = DatasetTableService.get_dataset_table_by_uri(session, data['tableUri'])
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        share_item = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == table.tableUri,
                    models.ShareObjectItem.status.in_(share_item_shared_states)
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
        session, environment_uri: str, dataset_uri: str
    ):
        """For a given dataset, returns the list of Tables shared with the environment
        This means looking at approved ShareObject items
        for the share object associating the dataset and environment
        """
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        env_tables_shared = (
            session.query(DatasetTable)  # all tables
            .join(
                models.ShareObjectItem,  # found in ShareObjectItem
                models.ShareObjectItem.itemUri == DatasetTable.tableUri,
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
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .all()
        )

        return env_tables_shared

    @staticmethod
    def get_dataset_tables_shared_with_env(
        session, environment_uri: str, dataset_uri: str
    ):
        return [
            {"tableUri": t.tableUri, "GlueTableName": t.GlueTableName}
            for t in DatasetTableService.query_dataset_tables_shared_with_env(
                session, environment_uri, dataset_uri
            )
        ]

    @staticmethod
    def get_dataset_table_by_uri(session, table_uri):
        table: DatasetTable = session.query(DatasetTable).get(table_uri)
        if not table:
            raise exceptions.ObjectNotFound('DatasetTable', table_uri)
        return table

    @staticmethod
    def sync_existing_tables(session, datasetUri, glue_tables=None):

        dataset: Dataset = session.query(Dataset).get(datasetUri)
        if dataset:
            existing_tables = (
                session.query(DatasetTable)
                .filter(DatasetTable.datasetUri == datasetUri)
                .all()
            )
            existing_table_names = [e.GlueTableName for e in existing_tables]
            existing_dataset_tables_map = {t.GlueTableName: t for t in existing_tables}

            DatasetTableService.update_existing_tables_status(existing_tables, glue_tables)
            logger.info(
                f'existing_tables={glue_tables}'
            )
            for table in glue_tables:
                if table['Name'] not in existing_table_names:
                    logger.info(
                        f'Storing new table: {table} for dataset db {dataset.GlueDatabaseName}'
                    )
                    updated_table = DatasetTable(
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
                    # ADD DATASET TABLE PERMISSIONS
                    env = Environment.get_environment_by_uri(session, dataset.environmentUri)
                    permission_group = set([dataset.SamlAdminGroupName, env.SamlGroupName, dataset.stewards if dataset.stewards is not None else dataset.SamlAdminGroupName])
                    for group in permission_group:
                        ResourcePolicy.attach_resource_policy(
                            session=session,
                            group=group,
                            permissions=permissions.DATASET_TABLE_READ,
                            resource_uri=updated_table.tableUri,
                            resource_type=DatasetTable.__name__,
                        )
                else:
                    logger.info(
                        f'Updating table: {table} for dataset db {dataset.GlueDatabaseName}'
                    )
                    updated_table: DatasetTable = (
                        existing_dataset_tables_map.get(table['Name'])
                    )
                    updated_table.GlueTableProperties = json_utils.to_json(
                        table.get('Parameters', {})
                    )

                DatasetTableService.sync_table_columns(session, updated_table, table)

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

        DatasetTableService.delete_all_table_columns(session, dataset_table)

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
            table_col = DatasetTableColumn(
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
        session.query(DatasetTableColumn).filter(
            and_(
                DatasetTableColumn.GlueDatabaseName
                == dataset_table.GlueDatabaseName,
                DatasetTableColumn.GlueTableName == dataset_table.GlueTableName,
            )
        ).delete()
        session.commit()

    @staticmethod
    def get_table_by_s3_prefix(session, s3_prefix, accountid, region):
        table: DatasetTable = (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.S3Prefix.startswith(s3_prefix),
                    DatasetTable.AWSAccountId == accountid,
                    DatasetTable.region == region,
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
