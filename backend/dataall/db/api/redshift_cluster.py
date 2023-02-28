import logging

from sqlalchemy import and_, or_, literal

from .. import models, api, exceptions, paginate, permissions
from . import has_resource_perm, ResourcePolicy, DatasetTable, Environment, Dataset
from ..models.Enums import ShareItemStatus
from ...utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from ...utils.slugify import slugify

log = logging.getLogger(__name__)


class RedshiftCluster:
    def __init__(self):
        pass

    @staticmethod
    @has_resource_perm(permissions.CREATE_REDSHIFT_CLUSTER)
    def create(session, username, groups, uri: str, data: dict = None, check_perm=None):

        RedshiftCluster.__validate_cluster_data(data, uri)

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data['SamlGroupName'],
            permission_name=permissions.CREATE_REDSHIFT_CLUSTER,
        )

        environment = Environment.get_environment_by_uri(session, uri)

        if not environment.warehousesEnabled:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_REDSHIFT_CLUSTER,
                message=f'Warehouses feature is disabled for the environment {environment.label}',
            )

        data['clusterName'] = slugify(data['label'], separator='')

        RedshiftCluster.validate_none_existing_cluster(
            session, data['clusterName'], environment
        )
        redshift_cluster = RedshiftCluster.create_redshift_cluster(
            session, username, data, environment
        )
        return redshift_cluster

    @staticmethod
    def create_redshift_cluster(
        session, username, cluster_input, environment: models.Environment
    ):
        redshift_cluster = models.RedshiftCluster(
            environmentUri=environment.environmentUri,
            organizationUri=environment.organizationUri,
            owner=cluster_input.get('owner', username),
            label=cluster_input['label'],
            description=cluster_input.get('description'),
            masterDatabaseName=cluster_input['masterDatabaseName'],
            masterUsername=cluster_input['masterUsername'],
            databaseName=cluster_input.get('databaseName', 'datahubdb'),
            nodeType=cluster_input['nodeType'],
            numberOfNodes=cluster_input['numberOfNodes'],
            port=cluster_input.get('port') or 5432,
            region=environment.region,
            AwsAccountId=environment.AwsAccountId,
            status='CREATING',
            vpc=cluster_input['vpc'],
            subnetIds=cluster_input.get('subnetIds'),
            securityGroupIds=cluster_input.get('securityGroupIds'),
            IAMRoles=[environment.EnvironmentDefaultIAMRoleArn],
            tags=cluster_input.get('tags', []),
            SamlGroupName=cluster_input['SamlGroupName'],
            imported=False,
        )
        session.add(redshift_cluster)
        session.commit()

        name = NamingConventionService(
            target_uri=redshift_cluster.clusterUri,
            target_label=redshift_cluster.label,
            pattern=NamingConventionPattern.DEFAULT,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        redshift_cluster.name = name
        redshift_cluster.clusterName = name
        redshift_cluster.CFNStackName = f'{name}-stack'
        redshift_cluster.CFNStackStatus = 'CREATING'
        redshift_cluster.kmsAlias = redshift_cluster.clusterName
        redshift_cluster.datahubSecret = f'{redshift_cluster.name}-redshift-dhuser'
        redshift_cluster.masterSecret = f'{redshift_cluster.name}-redshift-masteruser'

        activity = models.Activity(
            action='redshiftcluster:user:create',
            label='redshiftcluster:user:create',
            owner=username,
            summary=f'{username} '
            f'Created Redshift cluster {redshift_cluster.name} '
            f'on Environment {environment.name}|{environment.AwsAccountId}',
            targetUri=redshift_cluster.clusterUri,
            targetType='redshiftcluster',
        )
        session.add(activity)
        session.commit()

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=redshift_cluster.SamlGroupName,
            resource_uri=redshift_cluster.clusterUri,
            permissions=permissions.REDSHIFT_CLUSTER_ALL,
            resource_type=models.RedshiftCluster.__name__,
        )
        if environment.SamlGroupName != redshift_cluster.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=permissions.REDSHIFT_CLUSTER_ALL,
                resource_uri=redshift_cluster.clusterUri,
                resource_type=models.Dataset.__name__,
            )
        return redshift_cluster

    @staticmethod
    def __validate_cluster_data(data, uri):
        if not data:
            raise exceptions.RequiredParameter('input')
        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('SamlGroupName')
        if not uri:
            raise exceptions.RequiredParameter('environmentUri')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

    @staticmethod
    def validate_none_existing_cluster(session, cluster_name, environment):
        existing_cluster = (
            session.query(models.RedshiftCluster)
            .filter(
                and_(
                    models.RedshiftCluster.environmentUri == environment.environmentUri,
                    models.RedshiftCluster.clusterName == cluster_name,
                )
            )
            .first()
        )
        if existing_cluster:
            raise exceptions.ResourceAlreadyExists(
                'Create Redshift cluster',
                f'Redshift Cluster {cluster_name} '
                f'is already assigned to this environment {environment.name}',
            )

    @staticmethod
    def update(session, context, cluster_input, clusterUri):
        cluster = session.query(models.RedshiftCluster).get(clusterUri)
        if not cluster:
            raise exceptions.ObjectNotFound('RedshiftCluster', clusterUri)
        if 'name' in cluster_input.keys():
            cluster.name = cluster_input.get('name')
        if 'description' in cluster_input.keys():
            cluster.description = cluster_input.get('description')
        return cluster

    @staticmethod
    def get_redshift_cluster_by_uri(session, uri) -> models.RedshiftCluster:
        if not uri:
            raise exceptions.RequiredParameter('ClusterUri')
        cluster = session.query(models.RedshiftCluster).get(uri)
        if not cluster:
            raise exceptions.ObjectNotFound('RedshiftCluster', uri)
        return cluster

    @staticmethod
    @has_resource_perm(permissions.LIST_REDSHIFT_CLUSTER_DATASETS)
    def list_available_datasets(
        session, username, groups, uri: str, data: dict = None, check_perm=None
    ):
        cluster: models.RedshiftCluster = RedshiftCluster.get_redshift_cluster_by_uri(
            session, uri
        )
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()

        shared = (
            session.query(
                models.ShareObject.datasetUri.label('datasetUri'),
                literal(cluster.clusterUri).label('clusterUri'),
            )
            .join(
                models.RedshiftCluster,
                models.RedshiftCluster.environmentUri
                == models.ShareObject.environmentUri,
            )
            .filter(
                and_(
                    models.RedshiftCluster.clusterUri == cluster.clusterUri,
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    or_(
                        models.ShareObject.owner == username,
                        models.ShareObject.principalId.in_(groups),
                    ),
                )
            )
            .group_by(models.ShareObject.datasetUri, models.RedshiftCluster.clusterUri)
        )
        created = (
            session.query(
                models.Dataset.datasetUri.label('datasetUri'),
                models.RedshiftCluster.clusterUri.label('clusterUri'),
            )
            .filter(
                and_(
                    or_(
                        models.Dataset.owner == username,
                        models.Dataset.SamlAdminGroupName.in_(groups),
                    ),
                    models.RedshiftCluster.clusterUri == cluster.clusterUri,
                    models.Dataset.environmentUri
                    == models.RedshiftCluster.environmentUri,
                )
            )
            .group_by(models.Dataset.datasetUri, models.RedshiftCluster.clusterUri)
        )
        all_group_datasets_sub_query = shared.union(created).subquery(
            'all_group_datasets_sub_query'
        )
        query = (
            session.query(models.Dataset)
            .join(
                all_group_datasets_sub_query,
                models.Dataset.datasetUri == all_group_datasets_sub_query.c.datasetUri,
            )
            .outerjoin(
                models.RedshiftClusterDataset,
                and_(
                    models.RedshiftClusterDataset.datasetUri
                    == models.Dataset.datasetUri,
                    models.RedshiftClusterDataset.clusterUri == cluster.clusterUri,
                ),
            )
            .filter(
                and_(
                    all_group_datasets_sub_query.c.clusterUri == cluster.clusterUri,
                    models.RedshiftClusterDataset.datasetUri.is_(None),
                    models.Dataset.deleted.is_(None),
                )
            )
        )
        if data.get('term'):
            term = data.get('term')
            query = query.filter(
                or_(
                    models.Dataset.label.ilike('%' + term + '%'),
                    models.Dataset.tags.any(term),
                    models.Dataset.topics.any(term),
                )
            )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_REDSHIFT_CLUSTER_DATASETS)
    def list_cluster_datasets(
        session, username, groups, uri: str, data: dict = None, check_perm=None
    ):
        query = (
            session.query(models.Dataset)
            .join(
                models.RedshiftClusterDataset,
                models.Dataset.datasetUri == models.RedshiftClusterDataset.datasetUri,
            )
            .filter(
                models.RedshiftClusterDataset.clusterUri == uri,
            )
        )
        if data.get('term'):
            term = data.get('term')
            query = query.filter(
                or_(
                    models.Dataset.label.ilike('%' + term + '%'),
                    models.Dataset.tags.any(term),
                    models.Dataset.topics.any(term),
                )
            )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.LIST_REDSHIFT_CLUSTER_DATASETS)
    def list_available_cluster_tables(
        session, username, groups, uri: str, data: dict = None, check_perm=None
    ):
        cluster: models.RedshiftCluster = RedshiftCluster.get_redshift_cluster_by_uri(
            session, uri
        )
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()

        shared = (
            session.query(
                models.ShareObject.datasetUri.label('datasetUri'),
                models.ShareObjectItem.itemUri.label('tableUri'),
                literal(cluster.clusterUri).label('clusterUri'),
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .join(
                models.RedshiftCluster,
                models.RedshiftCluster.environmentUri
                == models.ShareObject.environmentUri,
            )
            .filter(
                and_(
                    models.RedshiftCluster.clusterUri == cluster.clusterUri,
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    or_(
                        models.ShareObject.owner == username,
                        models.ShareObject.principalId.in_(groups),
                    ),
                )
            )
            .group_by(
                models.ShareObject.datasetUri,
                models.ShareObjectItem.itemUri,
                models.RedshiftCluster.clusterUri,
            )
        )
        created = (
            session.query(
                models.DatasetTable.datasetUri.label('datasetUri'),
                models.DatasetTable.tableUri.label('tableUri'),
                models.RedshiftCluster.clusterUri.label('clusterUri'),
            )
            .join(
                models.Dataset,
                models.DatasetTable.datasetUri == models.Dataset.datasetUri,
            )
            .filter(
                and_(
                    or_(
                        models.Dataset.owner == username,
                        models.Dataset.SamlAdminGroupName.in_(groups),
                    ),
                    models.RedshiftCluster.clusterUri == cluster.clusterUri,
                    models.Dataset.environmentUri
                    == models.RedshiftCluster.environmentUri,
                )
            )
            .group_by(
                models.DatasetTable.datasetUri,
                models.DatasetTable.tableUri,
                models.RedshiftCluster.clusterUri,
            )
        )
        all_group_tables_sub_query = shared.union(created).subquery(
            'all_group_tables_sub_query'
        )
        query = (
            session.query(models.DatasetTable)
            .join(
                all_group_tables_sub_query,
                all_group_tables_sub_query.c.tableUri == models.DatasetTable.tableUri,
            )
            .filter(
                models.RedshiftCluster.clusterUri == cluster.clusterUri,
            )
        )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    @has_resource_perm(permissions.GET_REDSHIFT_CLUSTER)
    def get_cluster(session, username, groups, uri, data=None, check_perm=True):
        cluster = RedshiftCluster.get_redshift_cluster_by_uri(session, uri)
        return cluster

    @staticmethod
    @has_resource_perm(permissions.ADD_DATASET_TO_REDSHIFT_CLUSTER)
    def add_dataset(session, username, groups, uri, data=None, check_perm=True):
        cluster = RedshiftCluster.get_redshift_cluster_by_uri(session, uri)

        if cluster.status != 'available':
            raise exceptions.AWSResourceNotAvailable(
                action='ADD DATASET TO REDSHIFT CLUSTER',
                message=f'Cluster {cluster.name} is not on available state ({cluster.status})',
            )

        dataset = Dataset.get_dataset_by_uri(session, dataset_uri=data['datasetUri'])

        exists = session.query(models.RedshiftClusterDataset).get(
            (uri, data['datasetUri'])
        )
        if exists:
            raise exceptions.ResourceAlreadyExists(
                action='ADD DATASET TO REDSHIFT CLUSTER',
                message=f'Dataset {dataset.name} is already loaded to cluster {cluster.name}',
            )

        linked_dataset = models.RedshiftClusterDataset(
            clusterUri=uri, datasetUri=data['datasetUri']
        )
        session.add(linked_dataset)

        return cluster, dataset

    @staticmethod
    @has_resource_perm(permissions.REMOVE_DATASET_FROM_REDSHIFT_CLUSTER)
    def remove_dataset_from_cluster(
        session, username, groups, uri, data=None, check_perm=True
    ):
        cluster = RedshiftCluster.get_redshift_cluster_by_uri(session, uri)
        session.query(models.RedshiftClusterDatasetTable).filter(
            and_(
                models.RedshiftClusterDatasetTable.clusterUri == uri,
                models.RedshiftClusterDatasetTable.datasetUri == data['datasetUri'],
            )
        ).delete()
        session.commit()

        dataset = None
        exists = session.query(models.RedshiftClusterDataset).get(
            (uri, data['datasetUri'])
        )
        if exists:
            session.delete(exists)
            dataset = session.query(models.Dataset).get(data['datasetUri'])
            if not dataset:
                raise exceptions.ObjectNotFound('Dataset', data['datasetUri'])

        return cluster, dataset

    @staticmethod
    def list_all_cluster_datasets(session, clusterUri):
        cluster_datasets = (
            session.query(models.RedshiftClusterDataset)
            .filter(
                models.RedshiftClusterDataset.datasetUri.isnot(None),
                models.RedshiftClusterDataset.clusterUri == clusterUri,
            )
            .all()
        )
        return cluster_datasets

    @staticmethod
    def get_cluster_dataset(
        session, clusterUri, datasetUri
    ) -> models.RedshiftClusterDataset:
        cluster_dataset = (
            session.query(models.RedshiftClusterDataset)
            .filter(
                and_(
                    models.RedshiftClusterDataset.clusterUri == clusterUri,
                    models.RedshiftClusterDataset.datasetUri == datasetUri,
                )
            )
            .first()
        )
        if not cluster_dataset:
            raise Exception(
                f'Cluster {clusterUri} is not associated to dataset {datasetUri}'
            )
        return cluster_dataset

    @staticmethod
    def get_cluster_dataset_table(
        session, clusterUri, datasetUri, tableUri
    ) -> models.RedshiftClusterDatasetTable:
        cluster_dataset_table = (
            session.query(models.RedshiftClusterDatasetTable)
            .filter(
                and_(
                    models.RedshiftClusterDatasetTable.clusterUri == clusterUri,
                    models.RedshiftClusterDatasetTable.datasetUri == datasetUri,
                    models.RedshiftClusterDatasetTable.tableUri == tableUri,
                )
            )
            .first()
        )
        if not cluster_dataset_table:
            log.error(f'Table {tableUri} copy is not enabled on cluster')
        return cluster_dataset_table

    @staticmethod
    @has_resource_perm(permissions.ENABLE_REDSHIFT_TABLE_COPY)
    def enable_copy_table(
        session, username, groups, uri, data=None, check_perm=True
    ) -> models.RedshiftClusterDatasetTable:
        cluster = RedshiftCluster.get_redshift_cluster_by_uri(session, uri)
        table = DatasetTable.get_dataset_table_by_uri(session, data['tableUri'])
        table = models.RedshiftClusterDatasetTable(
            clusterUri=uri,
            datasetUri=data['datasetUri'],
            tableUri=data['tableUri'],
            enabled=True,
            schema=data['schema'] or f'datahub_{cluster.clusterUri}',
            databaseName=cluster.databaseName,
            dataLocation=f's3://{table.S3BucketName}/{data.get("dataLocation")}'
            if data.get('dataLocation')
            else table.S3Prefix,
        )
        session.add(table)
        session.commit()
        return table

    @staticmethod
    @has_resource_perm(permissions.DISABLE_REDSHIFT_TABLE_COPY)
    def disable_copy_table(
        session, username, groups, uri, data=None, check_perm=True
    ) -> bool:
        table = (
            session.query(models.RedshiftClusterDatasetTable)
            .filter(
                and_(
                    models.RedshiftClusterDatasetTable.clusterUri == uri,
                    models.RedshiftClusterDatasetTable.datasetUri == data['datasetUri'],
                    models.RedshiftClusterDatasetTable.tableUri == data['tableUri'],
                )
            )
            .first()
        )
        session.delete(table)
        session.commit()
        return True

    @staticmethod
    @has_resource_perm(permissions.LIST_REDSHIFT_CLUSTER_DATASETS)
    def list_copy_enabled_tables(
        session, username, groups, uri, data=None, check_perm=True
    ) -> [models.RedshiftClusterDatasetTable]:
        q = (
            session.query(models.DatasetTable)
            .join(
                models.RedshiftClusterDatasetTable,
                models.RedshiftClusterDatasetTable.tableUri
                == models.DatasetTable.tableUri,
            )
            .filter(models.RedshiftClusterDatasetTable.clusterUri == uri)
        )
        if data.get('term'):
            term = data.get('term')
            q = q.filter(
                models.DatasetTable.label.ilike('%' + term + '%'),
            )
        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    def delete_all_cluster_linked_objects(session, clusterUri):
        session.query(models.RedshiftClusterDatasetTable).filter(
            and_(
                models.RedshiftClusterDatasetTable.clusterUri == clusterUri,
            )
        ).delete()
        session.query(models.RedshiftClusterDataset).filter(
            models.RedshiftClusterDataset.clusterUri == clusterUri,
        ).delete()
        return True
