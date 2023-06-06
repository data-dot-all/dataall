import logging
import uuid

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger('aws:lakeformation')
PIVOT_ROLE_NAME_PREFIX = "dataallPivotRole"


class LakeFormation:
    def __init__(self):
        pass

    @staticmethod
    def check_existing_lf_registered_location(resource_arn, accountid, region):
        """
        Checks if there is a non-dataall-created registered location for the Dataset
        Returns False is already existing location else return the resource info
        """
        try:
            session = SessionHelper.remote_session(accountid)
            lf_client = session.client('lakeformation', region_name=region)
            response = lf_client.describe_resource(ResourceArn=resource_arn)
            registered_role_name = response['ResourceInfo']['RoleArn'].lstrip(f"arn:aws:iam::{accountid}:role/")
            log.info(f'LF data location already registered: {response}, registered with role {registered_role_name}')
            if registered_role_name.startswith(PIVOT_ROLE_NAME_PREFIX):
                log.info('The existing data location was created as part of the dataset stack. There was no pre-existing data location.')
                return False
            return response['ResourceInfo']

        except ClientError as e:
            log.info(f'LF data location for resource {resource_arn} not found due to {e}')
            return False

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
        target_principals = data['target_principals']
        source_database = data['source_database']
        source_table = data['source_table']
        source_accountid = data['source_accountid']
        for target_principal in target_principals:
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
