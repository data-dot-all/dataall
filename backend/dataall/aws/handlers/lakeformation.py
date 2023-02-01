import logging
import uuid

from botocore.exceptions import ClientError
from .service_handlers import Worker

from .sts import SessionHelper
from ... import db
from ...db import models

log = logging.getLogger('aws:lakeformation')


class LakeFormation:
    def __init__(self):
        pass

    @staticmethod
    def create_lf_client(accountid, region):
        session = SessionHelper.remote_session(accountid)
        lf_client = session.client('lakeformation', region_name=region)

        return lf_client

    @staticmethod
    def describe_resource(resource_arn, accountid, region):
        """
        Describes a LF data location
        """
        try:
            session = SessionHelper.remote_session(accountid)
            lf_client = session.client('lakeformation', region_name=region)

            response = lf_client.describe_resource(ResourceArn=resource_arn)

            log.debug(f'LF data location already registered: {response}')

            return response['ResourceInfo']

        except ClientError as e:
            log.error(
                f'LF data location for resource {resource_arn} not found due to {e}'
            )

    @staticmethod
    def grant_pivot_role_all_database_permissions(accountid, region, database):
        LakeFormation.grant_permissions_to_database(
            client=SessionHelper.remote_session(accountid=accountid).client(
                'lakeformation', region_name=region
            ),
            principals=[SessionHelper.get_delegation_role_arn(accountid)],
            database_name=database,
            permissions=['ALL'],
        )

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
                f'Granting database permissions {permissions} to {principal} on database {database_name}'
            )
            try:
                client.grant_permissions(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'Database': {'Name': database_name},
                    },
                    Permissions=permissions,
                )
                log.info(
                    f'Successfully granted principal {principal} permissions {permissions} '
                    f'to {database_name}'
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
                f'Could not grant principal {principal} '
                f'permissions {permissions} to table '
                f'{database_name}.{table_name} due to: {e}'
            )
            # raise e

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
            LakeFormation.batch_revoke_permissions(
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
            log.debug(
                f'Could not revoke IAMAllowedGroups Super '
                f'permission on table {database}|{table} due to {e}'
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
        log.info(f'Batch Revoking {entries}')
        entries_chunks: list = [entries[i : i + 20] for i in range(0, len(entries), 20)]
        failures = []
        try:
            for entries_chunk in entries_chunks:
                response = client.batch_revoke_permissions(
                    CatalogId=accountid, Entries=entries_chunk
                )
                log.info(f'Batch Revoke response: {response}')
                failures.extend(response.get('Failures'))

            for failure in failures:
                if not (
                    failure['Error']['ErrorCode'] == 'InvalidInputException'
                    and (
                        'Grantee has no permissions' in failure['Error']['ErrorMessage']
                        or 'No permissions revoked' in failure['Error']['ErrorMessage']
                        or 'not found' in failure['Error']['ErrorMessage']
                    )
                ):
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
            log.warning(f'Batch Revoke ended with failures: {failures}')
            raise e

    @staticmethod
    def grant_resource_link_permission_on_target(client, source, target):
        for principal in target['principals']:
            try:
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
                client.grant_permissions(**table_grant)
                log.info(
                    f'Successfully granted permissions DESCRIBE,SELECT to {principal} on target '
                    f'{source["accountid"]}://{source["database"]}/{source["tablename"]}'
                )
            except ClientError as e:
                logging.error(
                    f'Failed granting principal {principal} '
                    'read access to resource link on target'
                    f' {source["accountid"]}://{source["database"]}/{source["tablename"]} '
                    f'due to: {e}'
                )
                raise e

    @staticmethod
    def grant_resource_link_permission(client, source, target, target_database):
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
                # Resource link only supports DESCRIBE and DROP permissions no SELECT
                Permissions=['DESCRIBE'],
            )
            try:
                client.grant_permissions(**resourcelink_grant)
                log.info(
                    f'Granted resource link DESCRIBE access '
                    f'to principal {principal} on {target["accountid"]}://{target_database}/{source["tablename"]}'
                )
            except ClientError as e:
                logging.error(
                    f'Failed granting principal {principal} '
                    f'read access to resource link on {target["accountid"]}://{target_database}/{source["tablename"]} '
                    f'due to: {e}'
                )
                raise e

    @staticmethod
    def revoke_source_table_access(**data):
        """
        Revokes permissions for a principal in a cross account sharing setup
        Parameters
        ----------
        data :

        Returns
        -------

        """
        logging.info(f'Revoking source table access: {data} ...')
        target_accountid = data['target_accountid']
        region = data['region']
        target_principal = data['target_principal']
        source_database = data['source_database']
        source_table = data['source_table']
        source_accountid = data['source_accountid']

        try:
            aws_session = SessionHelper.remote_session(target_accountid)
            lakeformation = aws_session.client('lakeformation', region_name=region)

            logging.info('Revoking DESCRIBE permission...')
            lakeformation.revoke_permissions(
                Principal=dict(DataLakePrincipalIdentifier=target_principal),
                Resource=dict(
                    Table=dict(
                        CatalogId=source_accountid,
                        DatabaseName=source_database,
                        Name=source_table,
                    )
                ),
                Permissions=['DESCRIBE'],
                PermissionsWithGrantOption=[],
            )
            logging.info('Successfully revoked DESCRIBE permissions')

            logging.info('Revoking SELECT permission...')
            lakeformation.revoke_permissions(
                Principal=dict(DataLakePrincipalIdentifier=target_principal),
                Resource=dict(
                    TableWithColumns=dict(
                        CatalogId=source_accountid,
                        DatabaseName=source_database,
                        Name=source_table,
                        ColumnWildcard={},
                    )
                ),
                Permissions=['SELECT'],
                PermissionsWithGrantOption=[],
            )
            logging.info('Successfully revoked DESCRIBE permissions')

        except ClientError as e:
            logging.error(
                f'Failed to revoke permissions for {target_principal} '
                f'on source table {source_accountid}/{source_database}/{source_table} '
                f'due to: {e}'
            )
            raise e

    @staticmethod
    def create_or_update_lf_tag(accountid, lf_client, tag_name, tag_values):
        try:
            logging.info(f'Creating LF Tag {tag_name} ...')
            if type(tag_values) != list:
                tag_values=[tag_values]

            lf_client.create_lf_tag(
                CatalogId=accountid,
                TagKey=tag_name,
                TagValues=tag_values
            )
            logging.info(f'Successfully create LF Tag {tag_name}')

        except ClientError as e:
            logging.info(f'LF Tag {tag_name} already exists, skippping create attempting update...')
            try:
                lf_client.update_lf_tag(
                    CatalogId=accountid,
                    TagKey=tag_name,
                    TagValuesToAdd=tag_values
                )
            except ClientError as e:
                logging.info(f'LF Tag {tag_name} already has value {tag_values}, skippping update...')
                pass
        return

    @staticmethod
    @Worker.handler('lakeformation.column.assign.lftags')
    def update_column_lf_tags(engine, task: models.Task):
        with engine.scoped_session() as session:
            column: models.DatasetTableColumn = session.query(
                models.DatasetTableColumn
            ).get(task.targetUri)
        
        # Check if LF Tag Already Assigned to Resource
        logging.info(f'Check if LF Tag Already Assigned...')
        lf_client = LakeFormation.create_lf_client(column.AWSAccountId, column.region)
        table_tags = LakeFormation.get_table_lf_tags(
            lf=lf_client, 
            account=column.AWSAccountId,
            db_name=column.GlueDatabaseName,
            table_name=column.GlueTableName
        )

        # Create a Dictionary of Existing Tag Key Value Pairs on Resource
        logging.info(f'Check if LF Tag Already Assigned...')
        existing_tags = {}
        if table_tags.get('LFTagsOnColumns'):
            for tag in table_tags.get('LFTagsOnColumns'):
                if tag['Name'] == column.name:
                    for col_tag in tag["LFTags"]:
                        if col_tag["TagKey"] in existing_tags.keys():
                            existing_tags[col_tag["TagKey"]].append(col_tag["TagValues"])
                        else:
                            existing_tags[col_tag["TagKey"]] = col_tag["TagValues"]
        logging.info(f"Existing Tags: {existing_tags}")

        if column.lfTagKey:
            lftags_to_assign = {column.lfTagKey[i]: column.lfTagValue[i] for i in range(len(column.lfTagKey))}
            logging.info(f"Tags To Assign: {lftags_to_assign}")

            # For Each LF Tag To Assign Check if Already Assigned and Assign if Not
            for tagkey in lftags_to_assign:
                if tagkey in existing_tags.keys() and lftags_to_assign[tagkey] in existing_tags[tagkey]:
                    logging.info("Tag Already Assigned, skipping...")
                    existing_tags[tagkey].remove(lftags_to_assign[tagkey])
                    if len(existing_tags[tagkey]) == 0:
                        existing_tags.pop(tagkey)
                else:
                    logging.info(f"Assigning LF Tag {tagkey} with value {lftags_to_assign[tagkey]} to Table...")
                    LakeFormation.create_or_update_lf_tag(
                        accountid=column.AWSAccountId,
                        lf_client=lf_client,
                        tag_name=tagkey,
                        tag_values=[lftags_to_assign[tagkey]]
                    )
                    # try:
                    #     lf_client.create_lf_tag(
                    #         CatalogId=column.AWSAccountId,
                    #         TagKey=tagkey,
                    #         TagValues=[lftags_to_assign[tagkey]]
                    #     )
                    #     print(f'Successfully create LF Tag {tagkey}')
                    # except ClientError as e:
                    #     print(f'LF Tag {tagkey} already exists, skippping create attempting update...')
                    #     try:
                    #         lf_client.update_lf_tag(
                    #             CatalogId=column.AWSAccountId,
                    #             TagKey=tagkey,
                    #             TagValuesToAdd=[lftags_to_assign[tagkey]]
                    #         )
                    #     except ClientError as e:
                    #         print(f'LF Tag {tagkey} already has value {lftags_to_assign[tagkey]}, skippping update...')
                    #         pass

                    # Add Tag to Resource
                    lf_client.add_lf_tags_to_resource(
                        CatalogId=column.AWSAccountId,
                        Resource={
                            'TableWithColumns': {
                                'CatalogId': column.AWSAccountId,
                                'DatabaseName': column.GlueDatabaseName,
                                'Name': column.GlueTableName,
                                'ColumnNames': [column.name]
                            },
                        },
                        LFTags=[
                            {
                                'CatalogId': column.AWSAccountId,
                                'TagKey': tagkey,
                                'TagValues': [lftags_to_assign[tagkey]]
                            },
                        ]
                    )

        # Remove Existing Tags that are No Longer Assigned
        logging.info(f"Existing Tags: {existing_tags}")
        if len(existing_tags.keys()) > 0:
            for key in existing_tags:
                lf_client.remove_lf_tags_from_resource(
                    CatalogId=column.AWSAccountId,
                    Resource={
                        'TableWithColumns': {
                            'CatalogId': column.AWSAccountId,
                            'DatabaseName': column.GlueDatabaseName,
                            'Name': column.GlueTableName,
                            'ColumnNames': [column.name]
                        },
                    },
                    LFTags=[
                        {
                            'CatalogId': column.AWSAccountId,
                            'TagKey': key,
                            'TagValues': existing_tags[key]
                        },
                    ]
                )
        return True

    @staticmethod
    @Worker.handler('lakeformation.table.assign.lftags')
    def update_table_lf_tags(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset_table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
                session, task.targetUri
            )

        # Check if LF Tag Already Assigned to Resource
        logging.info(f'Check if LF Tag Already Assigned...')
        lf_client = LakeFormation.create_lf_client(dataset_table.AWSAccountId, dataset_table.region)
        table_tags = LakeFormation.get_table_lf_tags(
            lf=lf_client, 
            account=dataset_table.AWSAccountId,
            db_name=dataset_table.GlueDatabaseName,
            table_name=dataset_table.GlueTableName
        )

        # Create a Dictionary of Existing Tag Key Value Pairs on Resource
        logging.info(f'Check if LF Tag Already Assigned...')
        existing_tags = {}
        if table_tags.get('LFTagsOnTable'):
            for tag in table_tags.get('LFTagsOnTable'):
                if tag["TagKey"] in existing_tags.keys():
                    existing_tags[tag["TagKey"]].append(tag["TagValues"])
                else:
                    existing_tags[tag["TagKey"]] = tag["TagValues"]
        logging.info(f"Existing Tags: {existing_tags}")

        if dataset_table.lfTagKey:
            lftags_to_assign = {dataset_table.lfTagKey[i]: dataset_table.lfTagValue[i] for i in range(len(dataset_table.lfTagKey))}
            logging.info(f"Tags To Assign: {lftags_to_assign}")

            # For Each LF Tag To Assign Check if Already Assigned and Assign if Not
            for tagkey in lftags_to_assign:
                if tagkey in existing_tags.keys() and lftags_to_assign[tagkey] in existing_tags[tagkey]:
                    logging.info("Tag Already Assigned, skipping...")
                    existing_tags[tagkey].remove(lftags_to_assign[tagkey])
                    if len(existing_tags[tagkey]) == 0:
                        existing_tags.pop(tagkey)
                else:
                    logging.info(f"Assigning LF Tag {tagkey} with value {lftags_to_assign[tagkey]} to Table...")
                    LakeFormation.create_or_update_lf_tag(
                        accountid=dataset_table.AWSAccountId,
                        lf_client=lf_client,
                        tag_name=tagkey,
                        tag_values=[lftags_to_assign[tagkey]]
                    )
                    # try:
                    #     lf_client.create_lf_tag(
                    #         CatalogId=dataset_table.AWSAccountId,
                    #         TagKey=tagkey,
                    #         TagValues=[lftags_to_assign[tagkey]]
                    #     )
                    #     print(f'Successfully create LF Tag {tagkey}')
                    # except ClientError as e:
                    #     print(f'LF Tag {tagkey} already exists, skippping create attempting update...')
                    #     try:
                    #         lf_client.update_lf_tag(
                    #             CatalogId=dataset_table.AWSAccountId,
                    #             TagKey=tagkey,
                    #             TagValuesToAdd=[lftags_to_assign[tagkey]]
                    #         )
                    #     except ClientError as e:
                    #         print(f'LF Tag {tagkey} already has value {lftags_to_assign[tagkey]}, skippping update...')
                    #         pass

                    # Add Tag to Resource
                    logging.info(f'Adding LF Tag {tagkey} with Key {lftags_to_assign[tagkey]} to table {dataset_table.GlueTableName}...')
                    response = lf_client.add_lf_tags_to_resource(
                        CatalogId=dataset_table.AWSAccountId,
                        Resource={
                            'Table': {
                                'CatalogId': dataset_table.AWSAccountId,
                                'DatabaseName': dataset_table.GlueDatabaseName,
                                'Name': dataset_table.GlueTableName,
                            }
                        },
                        LFTags=[
                            {
                                'CatalogId': dataset_table.AWSAccountId,
                                'TagKey': tagkey,
                                'TagValues': [lftags_to_assign[tagkey]]
                            },
                        ]
                    )
                    logging.info(response)
        
        # Remove Existing Tags that are No Longer Assigned
        logging.info(f"Existing Tags: {existing_tags}")
        if len(existing_tags.keys()) > 0:
            for key in existing_tags:
                lf_client.remove_lf_tags_from_resource(
                    CatalogId=dataset_table.AWSAccountId,
                    Resource={
                        'Table': {
                            'CatalogId': dataset_table.AWSAccountId,
                            'DatabaseName': dataset_table.GlueDatabaseName,
                            'Name': dataset_table.GlueTableName,
                        }
                    },
                    LFTags=[
                        {
                            'CatalogId': dataset_table.AWSAccountId,
                            'TagKey': key,
                            'TagValues': existing_tags[key]
                        },
                    ]
                )

        return True


    @staticmethod
    def get_table_lf_tags(lf, account, db_name, table_name):
        table_tags = lf.get_resource_lf_tags(
            CatalogId=account,
            Resource={
                'Table': {
                    'CatalogId': account,
                    'DatabaseName': db_name,
                    'Name': table_name
                }
            },
            ShowAssignedLFTags=True
        )
        return table_tags

    @staticmethod
    def get_column_lf_tags(lf, account, db_name, table_name, column_name):
        table_tags = lf.get_resource_lf_tags(
            CatalogId=account,
            Resource={
                'Table': {
                    'CatalogId': account,
                    'DatabaseName': db_name,
                    'Name': table_name
                }
            },
            ShowAssignedLFTags=True
        )
        return table_tags


    @staticmethod
    def grant_lftag_data_permissions_to_principal(source_acct, source_region, principal, tag_name, tag_values, permissionsWithGrant=False):
        try:
            logging.info(f'Adding LF Tag {tag_name} Permissions for Principal {principal} in Account {source_acct}...')
            lf_client=LakeFormation.create_lf_client(accountid=source_acct, region=source_region)

            response = lf_client.batch_grant_permissions(
                CatalogId=source_acct,
                Entries=[
                    {
                        'Id': str(uuid.uuid4()),
                        'Principal':{'DataLakePrincipalIdentifier': principal},
                        'Resource':{
                            'LFTagPolicy': {
                                'CatalogId': source_acct,
                                'ResourceType': 'DATABASE',
                                'Expression': [{'TagKey': tag_name, 'TagValues': tag_values}]
                            }
                        },
                        'Permissions': ['DESCRIBE'],
                        'PermissionsWithGrantOption': ['DESCRIBE'] if permissionsWithGrant else []
                    },
                    {
                        'Id': str(uuid.uuid4()),
                        'Principal':{'DataLakePrincipalIdentifier': principal},
                        'Resource':{
                            'LFTagPolicy': {
                                'CatalogId': source_acct,
                                'ResourceType': 'TABLE',
                                'Expression': [{'TagKey': tag_name, 'TagValues': tag_values}]
                            }
                        },
                        'Permissions': ['SELECT', 'DESCRIBE'],
                        'PermissionsWithGrantOption': ['SELECT', 'DESCRIBE'] if permissionsWithGrant else []
                    }
                ]
            )
            logging.info(f'Successfully grant LF Tag Permissions to {principal}')

        except ClientError as e:
            logging.error(
                f'Failed to grant LF Tag Permissions for {principal} '
                f'due to: {e}'
            )
            raise e
        return True


    @staticmethod
    def grant_lftag_permissions_to_external_acct(source_acct, source_region, principal, tag_name, tag_values, permissions):
        lf_client = LakeFormation.create_lf_client(source_acct, source_region)
        lf_client.grant_permissions(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'LFTag': {
                            'CatalogId': source_acct,
                            'TagKey': tag_name,
                            'TagValues': tag_values
                        }
                    },
                    Permissions=permissions,
                )
        return True