import logging
import uuid

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger('aws:lakeformation')


class LakeFormation:
    def __init__(self):
        pass

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
        entries_chunks: list = [entries[i : i + 20] for i in range(0, len(entries), 20)]
        failures = []
        try:
            for entries_chunk in entries_chunks:
                response = client.batch_revoke_permissions(
                    CatalogId=accountid, Entries=entries_chunk
                )
                log.info(f'Batch Revoke {entries_chunk} response: {response}')
                failures.extend(response.get('Failures'))
        except ClientError as e:
            for failure in failures:
                if not (
                    failure['Error']['ErrorCode'] == 'InvalidInputException'
                    and (
                        'Grantee has no permissions' in failure['Error']['ErrorMessage']
                        or 'No permissions revoked' in failure['Error']['ErrorMessage']
                    )
                ):
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
