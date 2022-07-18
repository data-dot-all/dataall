import logging
import os
import sys
import time
import uuid
import json
from typing import Any

from botocore.exceptions import ClientError
from sqlalchemy import and_

from .. import db
from ..aws.handlers.glue import Glue
from ..aws.handlers.s3 import S3
from ..aws.handlers.quicksight import Quicksight
from ..aws.handlers.sts import SessionHelper
from ..db import get_engine
from ..db import models, exceptions
from ..searchproxy import connect
from ..utils.alarm_service import AlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


class ShareManager:
    def __init__(self):
        pass

    @staticmethod
    def approve_share(engine, share_uri):
        """
        Manages the approval of Glue tables sharing through LakeFormation
        :param engine:
        :param share_uri:
        :return:
        """
        with engine.scoped_session() as session:
            (
                env_group,
                dataset,
                share,
                shared_tables,
                shared_folers,
                source_environment,
                target_environment,
            ) = ShareManager.get_share_data(session, share_uri, ['Approved'])

            principals = [env_group.environmentIAMRoleArn]

            if target_environment.dashboardsEnabled:
                ShareManager.add_quicksight_group_to_shared_with_principals(
                    target_environment, principals
                )

            ShareManager.share_tables(
                session,
                share,
                source_environment,
                target_environment,
                shared_tables,
                principals,
            )

            ShareManager.clean_shared_database(
                session, dataset, shared_tables, target_environment
            )

            ShareManager.share_folders(
                session,
                share,
                target_environment,
                shared_folers,
                dataset,
                principals,
            )

            # ShareManager.clean_shared_folders()

        return True

    @staticmethod
    def share_tables(
        session,
        share: models.ShareObject,
        source_environment: models.Environment,
        target_environment: models.Environment,
        shared_tables: [models.DatasetTable],
        principals: [str],
    ):
        for table in shared_tables:

            share_item = ShareManager.get_share_item(session, share, table)

            ShareManager.update_share_item_status(
                session,
                share_item,
                models.ShareObjectStatus.Share_In_Progress.value,
            )

            try:
                data = {
                    'source': {
                        'accountid': source_environment.AwsAccountId,
                        'region': source_environment.region,
                        'database': table.GlueDatabaseName,
                        'tablename': table.GlueTableName,
                    },
                    'target': {
                        'accountid': target_environment.AwsAccountId,
                        'region': target_environment.region,
                        'principals': principals,
                    },
                }

                ShareManager.share_table_with_target_account(**data)

                ShareManager.accept_ram_invitation(**data)

                ShareManager.create_resource_link_on_target_account(**data)

                ShareManager.update_share_item_status(
                    session,
                    share_item,
                    models.ShareObjectStatus.Share_Succeeded.value,
                )

            except Exception as e:
                logging.error(
                    f'Failed to share table {table.GlueTableName} '
                    f'from source account {source_environment.AwsAccountId}//{source_environment.region} '
                    f'with target account {target_environment.AwsAccountId}/{target_environment.region}'
                    f'due to: {e}'
                )
                ShareManager.update_share_item_status(
                    session,
                    share_item,
                    models.ShareObjectStatus.Share_Failed.value,
                )
                AlarmService().trigger_table_sharing_failure_alarm(
                    table, share, target_environment
                )

    @staticmethod
    def share_folders(
        session,
        share: models.ShareObject,
        target_environment: models.Environment,
        shared_folders: [models.DatasetStorageLocation],
        dataset: models.Dataset,
        principal: [str]
    ):
        for folder in shared_folders:
            share_item = ShareManager.get_share_item(session, share, folder)

            ShareManager.update_share_item_status(
                session,
                share_item,
                models.ShareObjectStatus.Share_In_Progress.value
            )

            source_account_id = folder.AWSAccountId
            access_point_name = share_item.S3AccessPointName
            bucket_name = folder.S3BucketName
            dataset_admin = dataset.IAMDatasetAdminRoleArn
            target_account_id = target_environment.AwsAccountId
            folder_name = folder.S3Prefix

            try:
                if not ShareManager.manage_access_point_and_bucket_policy(
                    dataset_admin,
                    source_account_id,
                    bucket_name,
                    access_point_name,
                    target_account_id,
                    folder_name,
                ):
                    policy = S3.get_access_point_policy(source_account_id, access_point_name)
                    print('what we got is ', policy)
                    # policy = json.loads(policy)

                    # # Update principals and Resource = envs and folders
                    policy['Statement'][0]['Principal']['AWS'].append(f'arn:aws:iam:{target_environment.AwsAccountId}:root')
                    policy['Statement'][0]['Resource'].append(f'arn:aws:s3:{folder.region}:{source_account_id}:accesspoint/{access_point_name}/object/{folder.S3Prefix}/*')
                    policy = json.dumps(policy)
                    print('after update is ', policy)
                    print('type of policy: ', type(policy))
                    S3.attach_access_point_policy(folder, access_point_name, policy)

                ShareManager.update_share_item_status(
                    session,
                    share_item,
                    models.ShareObjectStatus.Share_Succeeded.value,
                )
            except Exception as e:
                logging.error(
                    f'Failed to share folder {folder.S3Prefix} '
                    f'from source account {folder.AWSAccountId}//{folder.region} '
                    f'with target account {target_environment.AwsAccountId}//{target_environment.region} '
                    f'due to: {e}'
                )
                ShareManager.update_share_item_status(
                    session,
                    share_item,
                    models.ShareObjectStatus.Share_Failed.value,
                )
                AlarmService().trigger_folder_sharing_failure_alarm(
                    folder, share, target_environment
                )

    @staticmethod
    def add_quicksight_group_to_shared_with_principals(target_environment, principals):
        try:
            group = Quicksight.describe_group(
                client=Quicksight.get_quicksight_client_in_identity_region(
                    target_environment.AwsAccountId
                ),
                AwsAccountId=target_environment.AwsAccountId,
            )
            if group and group.get('Group', {}).get('Arn'):
                principals.append(group['Group']['Arn'])
        except ClientError as e:
            log.warning(f'Failed to retrieve Quicksight . group due to: {e}')

    @staticmethod
    def share_table_with_target_account(**data):
        """
        Shares tables using Lake Formation and RAM only when cross account
        Sharing feature may take some extra seconds that is why we are retrying here
        :param data:
        :return:
        """
        source_accountid = data['source']['accountid']
        source_region = data['source']['region']
        source_session = SessionHelper.remote_session(accountid=source_accountid)
        source_lf_client = source_session.client(
            'lakeformation', region_name=source_region
        )
        target_accountid = data['target']['accountid']
        target_region = data['target']['region']

        try:

            ShareManager.revoke_iamallowedgroups_super_permission_from_table(
                source_lf_client,
                source_accountid,
                data['source']['database'],
                data['source']['tablename'],
            )

            time.sleep(5)

            ShareManager.grant_permissions_to_table(
                source_lf_client,
                target_accountid,
                data['source']['database'],
                data['source']['tablename'],
                ['DESCRIBE', 'SELECT'],
                ['DESCRIBE', 'SELECT'],
            )

            # Issue with ram associations taking more than 10 seconds
            time.sleep(15)

            log.info(
                f"Granted access to table {data['source']['tablename']} "
                f'to external account {target_accountid} '
            )
            return True

        except ClientError as e:
            logging.error(
                f'Failed granting access to table {data["source"]["tablename"]} '
                f'from {source_accountid} / {source_region} '
                f'to external account{target_accountid}/{target_region}'
                f'due to: {e}'
            )
            raise e

    @staticmethod
    def grant_permissions_to_database(
        client,
        principals,
        database_name,
        permissions,
        permissions_with_grant_options=None,
    ):
        for principal in principals:
            log.info(
                f'Grant full permissions to role {principals} on database {database_name}'
            )
            try:

                response = client.grant_permissions(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'Database': {'Name': database_name},
                    },
                    Permissions=permissions,
                )
                log.info(
                    f'Successfully granted principal {principal} permissions {permissions} '
                    f'to {database_name}: {response}'
                )
            except ClientError as e:
                log.error(
                    f'Could not grant permissions '
                    f'principal {principal} '
                    f'{permissions} to database {database_name} due to: {e}'
                )

    @staticmethod
    def grant_permissions_to_table(
        client,
        principal,
        database_name,
        table_name,
        permissions,
        permissions_with_grant_options=None,
    ):
        try:
            grant_dict = dict(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={'Table': {'DatabaseName': database_name, 'Name': table_name}},
                Permissions=permissions,
            )
            if permissions_with_grant_options:
                grant_dict[
                    'PermissionsWithGrantOption'
                ] = permissions_with_grant_options

            response = client.grant_permissions(**grant_dict)

            log.info(
                f'Successfully granted principal {principal} permissions {permissions} '
                f'to {database_name}.{table_name}: {response}'
            )
        except ClientError as e:
            log.warning(
                f'Could not grant principal {principal}'
                f'permissions {permissions} to table '
                f'{database_name}.{table_name} due to: {e}'
            )
            # raise e

    @staticmethod
    def create_resource_link_on_target_account(**data):
        """
        When table is shared via Lake Formation from source account
        A Glue resource link is created on the target account and the target database
        :param data:
        :return:
        """
        source = data['source']
        target = data['target']
        target_session = SessionHelper.remote_session(accountid=target['accountid'])
        lakeformation_client = target_session.client(
            'lakeformation', region_name=target['region']
        )
        target_database = f"{source['database']}shared"
        resource_link_input = {
            'Name': source['tablename'],
            'TargetTable': {
                'CatalogId': data['source']['accountid'],
                'DatabaseName': source['database'],
                'Name': source['tablename'],
            },
        }

        # Creates the database if it doesnt exist
        try:

            Glue._create_table(
                **{
                    'accountid': target['accountid'],
                    'region': target['region'],
                    'database': target_database,
                    'tablename': source['tablename'],
                    'table_input': resource_link_input,
                }
            )
            ShareManager.grant_permissions_to_database(
                lakeformation_client, target['principals'], target_database, ['ALL']
            )

            ShareManager.grant_resource_link_permission(
                lakeformation_client, source, target, target_database
            )

            ShareManager.grant_resource_link_permission_on_target(
                lakeformation_client, source, target
            )

            log.info(
                f'Granted resource link SELECT read access on target '
                f"to principals {target['principals']}"
            )

        except ClientError as e:
            log.warning(
                f'Resource Link {resource_link_input} was not created because: {e}'
            )
            raise e

    @staticmethod
    def grant_resource_link_permission_on_target(client, source, target):
        for principal in target['principals']:
            table_grant = dict(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'TableWithColumns': {
                        'DatabaseName': source['database'],
                        'Name': source['tablename'],
                        'ColumnWildcard': {},
                        'CatalogId': source['accountid'],
                    }
                },
                Permissions=['DESCRIBE', 'SELECT'],
                PermissionsWithGrantOption=[],
            )
            response = client.grant_permissions(**table_grant)
            log.info(
                f'Successfully granted permission to {principal} on target {source["tablename"]}: {response}'
            )

    @staticmethod
    def grant_resource_link_permission(
        lakeformation_client, source, target, target_database
    ):
        for principal in target['principals']:
            resourcelink_grant = dict(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'Table': {
                        'DatabaseName': target_database,
                        'Name': source['tablename'],
                        'CatalogId': target['accountid'],
                    }
                },
                Permissions=['DESCRIBE', 'DROP', 'ALL'],
                PermissionsWithGrantOption=[],
            )
            try:
                response = lakeformation_client.grant_permissions(**resourcelink_grant)
                log.info(
                    f'Granted resource link DESCRIBE access '
                    f'to project {principal} with response: {response}'
                )
            except ClientError as e:
                logging.error(
                    f'Failed granting {resourcelink_grant} to project role {principal} '
                    f'read access to resource link {source["tablename"]} '
                    f'due to: {e}'
                )

    @staticmethod
    def get_resource_share_invitations(client, resource_share_arn):
        try:
            # Accepting one ram invitation
            # response = client.get_resource_share_invitations(
            #   resourceShareArns=[resource_share_arn]
            # )
            # Accepting All RAM invitations
            response = client.get_resource_share_invitations()
            invitation_list = response.get('resourceShareInvitations', [])
            return invitation_list
        except ClientError as e:
            log.error(
                f'Failed retrieving RAM resource '
                f'share invitations {resource_share_arn} due to {e}'
            )
            raise e

    @staticmethod
    def accept_resource_share_invitation(client, resource_share_invitation_arn):
        try:
            response = client.accept_resource_share_invitation(
                resourceShareInvitationArn=resource_share_invitation_arn
            )
            log.info(f'Accepted ram invitation {resource_share_invitation_arn}')
            return response.get('resourceShareInvitation')
        except ClientError as e:
            if (
                e.response['Error']['Code'] ==
                'ResourceShareInvitationAlreadyAcceptedException'
            ):
                log.info(
                    f'Failed to accept RAM invitation '
                    f'{resource_share_invitation_arn} already accepted'
                )
            else:
                log.error(
                    f'Failed to accept RAM invitation '
                    f'{resource_share_invitation_arn} due to {e}'
                )
                raise e

    @staticmethod
    def accept_ram_invitation(**data):
        """
        Accepts RAM invitations on the target account
        """
        source = data['source']
        target = data['target']
        target_session = SessionHelper.remote_session(accountid=target['accountid'])
        ram = target_session.client('ram', region_name=target['region'])
        resource_share_arn = (
            f'arn:aws:glue:{source["region"]}:{source["accountid"]}:'
            f'table/{data["source"]["database"]}/{data["source"]["tablename"]}'
        )
        ram_invitations = ShareManager.get_resource_share_invitations(
            ram, resource_share_arn
        )
        for invitation in ram_invitations:
            ShareManager.accept_resource_share_invitation(
                ram, invitation['resourceShareInvitationArn']
            )
            # Ram invitation acceptance is slow
            time.sleep(5)
        return True

    @staticmethod
    def revoke_iamallowedgroups_super_permission_from_table(
        client, accountid, database, table
    ):
        """
        When upgrading to LF tables can still have IAMAllowedGroups permissions
        Unless this is revoked the table can not be shared using LakeFormation
        :param client:
        :param accountid:
        :param database:
        :param table:
        :return:
        """
        try:
            log.info(
                f'Revoking IAMAllowedGroups Super '
                f'permission for table {database}|{table}'
            )
            ShareManager.batch_revoke_permissions(
                client,
                accountid,
                entries=[
                    {
                        'Id': str(uuid.uuid4()),
                        'Principal': {'DataLakePrincipalIdentifier': 'EVERYONE'},
                        'Resource': {
                            'Table': {
                                'DatabaseName': database,
                                'Name': table,
                                'CatalogId': accountid,
                            }
                        },
                        'Permissions': ['ALL'],
                        'PermissionsWithGrantOption': [],
                    }
                ],
            )
        except ClientError as e:
            log.warning(
                f'Cloud not revoke IAMAllowedGroups Super '
                f'permission on table {database}|{table} due to {e}'
            )

    @staticmethod
    def clean_shared_database(session, dataset, shared_tables, target_environment):
        shared_glue_tables = Glue.list_glue_database_tables(
            accountid=target_environment.AwsAccountId,
            database=dataset.GlueDatabaseName + 'shared',
            region=target_environment.region,
        )
        shared_tables = [t.GlueTableName for t in shared_tables]
        log.info(
            f'Shared database {dataset.GlueDatabaseName}shared glue tables: {shared_glue_tables}'
        )
        log.info(f'Share items of the share object {shared_tables}')
        tables_to_delete = []
        aws_session = SessionHelper.remote_session(accountid=dataset.AwsAccountId)
        client = aws_session.client('lakeformation', region_name=dataset.region)
        for table in shared_glue_tables:
            if table['Name'] not in shared_tables:
                log.info(
                    f'Found a table not part of the share: {dataset.GlueDatabaseName}//{table["Name"]}'
                )
                is_shared = (
                    session.query(models.ShareObjectItem)
                    .join(
                        models.ShareObject,
                        models.ShareObjectItem.shareUri == models.ShareObject.shareUri,
                    )
                    .filter(
                        and_(
                            models.ShareObjectItem.GlueTableName == table['Name'],
                            models.ShareObject.datasetUri == dataset.datasetUri,
                            models.ShareObject.status == 'Approved',
                            models.ShareObject.environmentUri ==
                            target_environment.environmentUri,
                        )
                    )
                    .first()
                )

                if not is_shared:
                    log.info(
                        f'Access to table {dataset.AwsAccountId}//{dataset.GlueDatabaseName}//{table["Name"]} '
                        f'will be removed for account {target_environment.AwsAccountId}'
                    )
                    if Glue.table_exists(
                        **{
                            'accountid': dataset.AwsAccountId,
                            'region': dataset.region,
                            'database': dataset.GlueDatabaseName,
                            'tablename': table['Name'],
                        }
                    ):
                        ShareManager.batch_revoke_permissions(
                            client,
                            target_environment.AwsAccountId,
                            [
                                {
                                    'Id': str(uuid.uuid4()),
                                    'Principal': {
                                        'DataLakePrincipalIdentifier': target_environment.AwsAccountId
                                    },
                                    'Resource': {
                                        'TableWithColumns': {
                                            'DatabaseName': dataset.GlueDatabaseName,
                                            'Name': table['Name'],
                                            'ColumnWildcard': {},
                                            'CatalogId': dataset.AwsAccountId,
                                        }
                                    },
                                    'Permissions': ['SELECT'],
                                    'PermissionsWithGrantOption': ['SELECT'],
                                }
                            ],
                        )

                tables_to_delete.append(table['Name'])

        if tables_to_delete:
            log.info(
                f'Deleting: {tables_to_delete} from shared database {dataset.GlueDatabaseName}shared'
            )
            Glue.batch_delete_tables(
                **{
                    'accountid': target_environment.AwsAccountId,
                    'region': target_environment.region,
                    'database': dataset.GlueDatabaseName + 'shared',
                    'tables': tables_to_delete,
                }
            )

    @staticmethod
    def batch_revoke_permissions(client, accountid, entries):
        """
        Batch revoke permissions to entries
        Retry is set for api throttling
        :param client:
        :param accountid:
        :param entries:
        :return:
        """
        entries_chunks: list = [entries[i: i + 20] for i in range(0, len(entries), 20)]
        failures = []
        try:
            for entries_chunk in entries_chunks:
                response = client.batch_revoke_permissions(
                    CatalogId=accountid, Entries=entries_chunk
                )
                log.info(f'Batch Revoke {entries_chunk} response: {response}')
                failures.extend(response.get('Failures'))
            if failures:
                raise ClientError(
                    error_response={
                        'Error': {
                            'Code': 'LakeFormation.batch_revoke_permissions',
                            'Message': f'Operation ended with failures: {failures}',
                        }
                    },
                    operation_name='LakeFormation.batch_revoke_permissions',
                )
        except ClientError as e:
            for failure in failures:
                if not (
                    failure['Error']['ErrorCode'] == 'InvalidInputException' and
                    (
                        'Grantee has no permissions' in failure['Error']['ErrorMessage'] or
                        'No permissions revoked' in failure['Error']['ErrorMessage']
                    )
                ):
                    log.warning(f'Batch Revoke ended with failures: {failures}')
                    raise e

    @staticmethod
    def reject_share(engine, share_uri):
        """
        Revokes access to the environment group that tables were share with
        If there is no other approved share object for the same environment
        Then revoke access to the AWS account on LakeFormation and delete the resource links
        :param engine:
        :param share_uri:
        :return:
        """

        with engine.scoped_session() as session:
            (
                env_group,
                dataset,
                share,
                shared_tables,
                source_environment,
                target_environment,
            ) = ShareManager.get_share_data(session, share_uri, ['Rejected'])

            log.info(f'Revoking permissions for tables : {shared_tables}')

            ShareManager.revoke_resource_links_access_on_target_account(
                session, env_group, share, shared_tables, target_environment
            )

            ShareManager.delete_resource_links_on_target_account(
                dataset, shared_tables, target_environment
            )

            ShareManager.clean_shared_database(
                session, dataset, shared_tables, target_environment
            )

            if not ShareManager.other_approved_share_object_exists(
                session, target_environment.environmentUri
            ):
                ShareManager.revoke_external_account_access_on_source_account(
                    shared_tables, source_environment, target_environment
                )

        return True

    @staticmethod
    def revoke_external_account_access_on_source_account(
        shared_tables, source_environment, target_environment
    ):
        log.info(f'Revoking Access for AWS account: {target_environment.AwsAccountId}')
        aws_session = SessionHelper.remote_session(
            accountid=source_environment.AwsAccountId
        )
        client = aws_session.client(
            'lakeformation', region_name=source_environment.region
        )
        revoke_entries = []
        for table in shared_tables:
            revoke_entries.append(
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {
                        'DataLakePrincipalIdentifier': target_environment.AwsAccountId
                    },
                    'Resource': {
                        'TableWithColumns': {
                            'DatabaseName': table.GlueDatabaseName,
                            'Name': table.GlueTableName,
                            'ColumnWildcard': {},
                            'CatalogId': source_environment.AwsAccountId,
                        }
                    },
                    'Permissions': ['SELECT'],
                    'PermissionsWithGrantOption': ['SELECT'],
                }
            )
            ShareManager.batch_revoke_permissions(
                client, target_environment.AwsAccountId, revoke_entries
            )

    @staticmethod
    def delete_resource_links_on_target_account(
        dataset, shared_tables, target_environment
    ):
        resource_links = [table.GlueTableName for table in shared_tables]
        log.info(f'Deleting resource links {resource_links}')
        return Glue.batch_delete_tables(
            **{
                'accountid': target_environment.AwsAccountId,
                'region': target_environment.region,
                'database': dataset.GlueDatabaseName + 'shared',
                'tables': resource_links,
            }
        )

    @staticmethod
    def revoke_resource_links_access_on_target_account(
        session, env_group, share, shared_tables, target_environment
    ):
        aws_session = SessionHelper.remote_session(
            accountid=target_environment.AwsAccountId
        )
        client = aws_session.client(
            'lakeformation', region_name=target_environment.region
        )
        revoke_entries = []
        for table in shared_tables:
            share_item = ShareManager.get_share_item(session, share, table)

            ShareManager.update_share_item_status(
                session, share_item, models.ShareObjectStatus.Revoke_In_Progress.value
            )
            try:
                data = {
                    'accountid': target_environment.AwsAccountId,
                    'region': target_environment.region,
                    'database': table.GlueDatabaseName + 'shared',
                    'tablename': table.GlueTableName,
                }
                log.info(f'Starting revoke for: {data}')

                if Glue.table_exists(**data):
                    revoke_entries.append(
                        {
                            'Id': str(uuid.uuid4()),
                            'Principal': {
                                'DataLakePrincipalIdentifier': env_group.environmentIAMRoleArn
                            },
                            'Resource': {
                                'Table': {
                                    'DatabaseName': table.GlueDatabaseName + 'shared',
                                    'Name': table.GlueTableName,
                                    'CatalogId': target_environment.AwsAccountId,
                                }
                            },
                            'Permissions': ['ALL', 'DESCRIBE', 'DROP'],
                        }
                    )

                    log.info(f'Revoking permissions for entries : {revoke_entries}')

                    ShareManager.batch_revoke_permissions(
                        client, target_environment.AwsAccountId, revoke_entries
                    )

                    ShareManager.update_share_item_status(
                        session,
                        share_item,
                        models.ShareObjectStatus.Revoke_Share_Succeeded.value,
                    )
            except Exception as e:
                logging.error(
                    f'Failed to revoke LF permissions to  table share {table.GlueTableName} '
                    f'on target account {target_environment.AwsAccountId}/{target_environment.region}'
                    f'due to: {e}'
                )
                ShareManager.update_share_item_status(
                    session,
                    share_item,
                    models.ShareObjectStatus.Revoke_Share_Failed.value,
                )
                AlarmService().trigger_revoke_sharing_failure_alarm(
                    table, share, target_environment
                )

    @staticmethod
    def get_share_data(session, share_uri, status):
        share: models.ShareObject = session.query(models.ShareObject).get(share_uri)
        dataset: models.Dataset = session.query(models.Dataset).get(share.datasetUri)
        source_environment: models.Environment = (
            db.api.Environment.get_environment_by_uri(session, dataset.environmentUri)
        )
        target_environment: models.Environment = (
            db.api.Environment.get_environment_by_uri(session, share.environmentUri)
        )
        shared_tables = db.api.DatasetTable.get_dataset_tables_shared_with_env(
            session,
            dataset_uri=dataset.datasetUri,
            environment_uri=target_environment.environmentUri,
            status=status,
        )
        share_folders = db.api.DatasetStorageLocation.get_dataset_locations_shared_with_env(
            session,
            dataset_uri=dataset.datasetUri,
            share_uri=share_uri,
            status=status,
        )
        env_group: models.EnvironmentGroup = (
            session.query(models.EnvironmentGroup)
            .filter(
                and_(
                    models.EnvironmentGroup.environmentUri == share.environmentUri,
                    models.EnvironmentGroup.groupUri == share.principalId,
                )
            )
            .first()
        )
        if not env_group:
            raise Exception(
                f'Share object Team {share.principalId} is not a member of the '
                f'environment {target_environment.name}/{target_environment.AwsAccountId}'
            )
        return (
            env_group,
            dataset,
            share,
            shared_tables,
            share_folders,
            source_environment,
            target_environment,
        )

    @staticmethod
    def other_approved_share_object_exists(session, environment_uri):
        return (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.Environment.environmentUri == environment_uri,
                    models.ShareObject.status ==
                    models.Enums.ShareObjectStatus.Approved.value,
                )
            )
            .all()
        )

    @staticmethod
    def get_share_item(
        session,
        share: models.ShareObject,
        share_category: Any,
    ) -> models.ShareObjectItem:
        if isinstance(share_category, models.DatasetTable):
            category_uri = share_category.tableUri
        elif isinstance(share_category, models.DatasetStorageLocation):
            category_uri = share_category.locationUri
        else:
            raise exceptions.InvalidInput(
                'share_category',
                share_category,
                'DatasetTable or DatasetStorageLocation'
            )
        share_item: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == category_uri,
                    models.ShareObjectItem.shareUri == share.shareUri,
                )
            )
            .first()
        )

        if not share_item:
            raise exceptions.ObjectNotFound('ShareObjectItem', category_uri)

        return share_item

    @staticmethod
    def update_share_item_status(
        session,
        share_item: models.ShareObjectItem,
        status: str,
    ) -> models.ShareObjectItem:

        log.info(f'Updating share item status to {status}')
        share_item.status = status
        session.commit()
        return share_item

    @staticmethod
    def manage_access_point_and_bucket_policy(
        dataset_admin: str,
        account_id: str,
        bucket_name: str,
        access_point_name: str,
        target_account_id: str,
        folder_name: str
    ):
        if not S3.get_bucket_access_point(account_id, access_point_name):
            access_point = S3.create_bucket_access_point(account_id, bucket_name, access_point_name)
            bucket_policy = json.loads(S3.get_bucket_policy(account_id, bucket_name))
            dataset_admin = SessionHelper.extract_account_from_role_arn(dataset_admin)
            exceptions_roleId = [
                f'{item}:*' for item in [
                    SessionHelper.get_role_id(account_id, 'dataallPivotRole'),
                    SessionHelper.get_role_id(account_id, dataset_admin)
                ]
            ]
            allow_owner_access = {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringLike": {
                        "aws:userId": exceptions_roleId
                    }
                }
            }
            delegated_to_accesspoint = {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringEquals": {
                        "s3:DataAccessPointArn": f"{access_point['AccessPointArn']}"
                    }
                }
            }
            bucket_policy['Statement'].append(allow_owner_access)
            bucket_policy['Statement'].append(delegated_to_accesspoint)
            S3.create_bucket_policy(account_id, bucket_name, json.dumps(bucket_policy))
            access_point_policy = {
                'Version': '2012-10-17',
                "Statement": [
                    {
                        "Sid": "AllowListFolderToIamRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{target_account_id}:root"
                        },
                        "Action": "s3:ListBucket",
                        "Resource": f"{access_point['AccessPointArn']}",
                        "Condition": {
                            "StringLike": {
                                "s3:prefix": f"{folder_name}/*"
                            }
                        }
                    },
                    {
                        "Sid": "AllowReadAccessToIamRole",
                        "Effect": "Allow",
                        "Principal": {
                            'AWS': f'arn:aws:iam::{target_account_id}:root'
                        },
                        "Action": "s3:GetObject",
                        "Resource": f"{access_point['AccessPointArn']}/object/{folder_name}/*",
                    }
                ]
            }
            S3.attach_access_point_policy(account_id, access_point_name, json.dumps(access_point_policy))
            return True
        else:
            return False


if __name__ == '__main__':

    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    ES = connect(envname=ENVNAME)

    share_uri = os.getenv('shareUri')
    share_item_uri = os.getenv('shareItemUri')
    handler = os.getenv('handler')

    if handler == 'approve_share':
        log.info(f'Starting approval task for share : {share_uri}...')
        ShareManager.approve_share(engine=ENGINE, share_uri=share_uri)

    elif handler == 'reject_share':
        log.info(f'Starting revoke task for share : {share_uri}...')
        ShareManager.reject_share(engine=ENGINE, share_uri=share_uri)

    log.info('Sharing task finished successfully')
