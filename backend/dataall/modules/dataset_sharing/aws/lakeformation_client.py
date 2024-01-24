import logging
import uuid
import time

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger('aws:lakeformation')


class LakeFormationClient:
    def __init__(self, account_id, region):
        self._session = SessionHelper.remote_session(accountid=account_id)
        self._client = self._session.client(
            'lakeformation', region_name=region
        )

    def grant_permissions_to_database(
        self,
        principals,
        database_name,
        permissions,
    ):
        for principal in principals:
            try:
                self._client.grant_permissions(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'Database': {'Name': database_name},
                    },
                    Permissions=permissions,
                )
                log.info(
                    f'Successfully granted principal {principal} '
                    f'Database permissions {permissions} '
                    f'to {database_name}'
                )
            except ClientError as e:
                log.error(
                    f'Could not grant principal {principal} '
                    f'Database permissions {permissions} '
                    f'to {database_name} due to: {e}'
                )
                raise e

    def grant_permissions_to_table(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None,
    ):
        for principal in principals:
            try:
                grant_dict = dict(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'Table': {
                            'DatabaseName': database_name,
                            'Name': table_name,
                            'CatalogId': catalog_id,
                        }
                    },
                    Permissions=permissions,
                )
                if permissions_with_grant_options:
                    grant_dict[
                        'PermissionsWithGrantOption'
                    ] = permissions_with_grant_options

                response = self._client.grant_permissions(**grant_dict)

                log.info(
                    f'Successfully granted principal {principal} '
                    f'Table permissions {permissions} '
                    f'to {catalog_id}://{database_name}/{table_name}  '
                    f'response: {response}'
                )
            except ClientError as e:
                log.warning(
                    f'Could not grant principal {principal} '
                    f'Table permissions {permissions} '
                    f'to {catalog_id}://{database_name}/{table_name}  '
                    f'due to: {e}'
                )
                raise e

    def grant_permissions_to_table_with_columns(
            self,
            principals,
            database_name,
            table_name,
            catalog_id,
            permissions,
            permissions_with_grant_options=None,
    ):
        for principal in principals:
            try:
                grant_dict = dict(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'TableWithColumns': {
                            'DatabaseName': database_name,
                            'Name': table_name,
                            'ColumnWildcard': {},
                            'CatalogId': catalog_id,
                        }
                    },
                    Permissions=permissions,
                )
                if permissions_with_grant_options:
                    grant_dict[
                        'PermissionsWithGrantOption'
                    ] = permissions_with_grant_options
                response = self._client.grant_permissions(**grant_dict)
                log.info(
                    f'Successfully granted principal {principal} '
                    f'TableWithColumns permissions {permissions} '
                    f'to {catalog_id}://{database_name}/{table_name} '
                    f'response: {response}'
                )
            except ClientError as e:
                log.error(
                    f'Failed granting principal {principal} '
                    f'TableWithColumns permissions {permissions}'
                    f'to {catalog_id}://{database_name}/{table_name} '
                    f'due to: {e}'
                )
                raise e

    def batch_revoke_permissions_from_table(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None
    ):
        """
        Batch revoke permissions to entries
        Retry is set for api throttling
        :param client:
        :param catalog_id:
        :param entries:
        :return:
        """
        entries = []
        for principal in principals:
            log.info(
                f'Revoking permissions {permissions} '
                f'on {catalog_id}/{database_name}/{table_name} '
                f'for principal {principal}'

            )
            revoke_dict = dict(
                Id=str(uuid.uuid4()),
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'Table': {
                        'DatabaseName': database_name,
                        'Name': table_name,
                        'CatalogId': catalog_id,
                    }
                },
                Permissions=permissions,
            )
            if permissions_with_grant_options:
                revoke_dict[
                    'PermissionsWithGrantOption'
                ] = permissions_with_grant_options

            entries.append(revoke_dict)

        log.info(f'Batch Revoking {entries}')
        entries_chunks: list = [entries[i : i + 20] for i in range(0, len(entries), 20)]
        failures = []
        try:
            for entries_chunk in entries_chunks:
                response = self._client.batch_revoke_permissions(
                    CatalogId=catalog_id, Entries=entries_chunk
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
                                'Code': 'LakeFormationClient.batch_revoke_permissions',
                                'Message': f'Operation ended with failures: {failures}',
                            }
                        },
                        operation_name='LakeFormationClient.batch_revoke_permissions',
                    )

        except ClientError as e:
            log.warning(f'Batch Revoke ended with failures: {failures}')
            raise e

    def batch_revoke_permissions_from_table_with_columns(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None
    ):
        """
        Batch revoke permissions to entries
        Retry is set for api throttling
        :param client:
        :param catalog_id:
        :param entries:
        :return:
        """
        entries = []
        for principal in principals:
            log.info(
                f'Revoking TableWithColumns permissions {permissions} '
                f'on {catalog_id}/{database_name}/{table_name} '
                f'for principal {principal}'

            )
            revoke_dict = dict(
                Id=str(uuid.uuid4()),
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource={
                    'TableWithColumns': {
                        'DatabaseName': database_name,
                        'Name': table_name,
                        'ColumnWildcard': {},
                        'CatalogId': catalog_id,
                    }
                },
                Permissions=permissions,
            )
            if permissions_with_grant_options:
                revoke_dict[
                    'PermissionsWithGrantOption'
                ] = permissions_with_grant_options

            entries.append(revoke_dict)

        log.info(f'Batch Revoking {entries}')
        entries_chunks: list = [entries[i : i + 20] for i in range(0, len(entries), 20)]
        failures = []
        try:
            for entries_chunk in entries_chunks:
                response = self._client.batch_revoke_permissions(
                    CatalogId=catalog_id, Entries=entries_chunk
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
                                'Code': 'LakeFormationClient.batch_revoke_permissions',
                                'Message': f'Operation ended with failures: {failures}',
                            }
                        },
                        operation_name='LakeFormationClient.batch_revoke_permissions',
                    )

        except ClientError as e:
            log.error(f'Batch Revoke TableWithColumns ended with failures: {failures}')
            raise e

    def revoke_permissions_from_table(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None
    ):
        for principal in principals:
            try:
                revoke_dict = dict(
                    Id=str(uuid.uuid4()),
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'Table': {
                            'DatabaseName': database_name,
                            'Name': table_name,
                            'CatalogId': catalog_id,
                        }
                    },
                    Permissions=permissions,
                )
                if permissions_with_grant_options:
                    revoke_dict[
                        'PermissionsWithGrantOption'
                    ] = permissions_with_grant_options

                response = self._client.revoke_permissions(**revoke_dict)
                time.sleep(1)
                log.info(
                    f'Successfully revoked principal {principal} '
                    f'Table permissions {permissions} '
                    f'to {catalog_id}://{database_name}/{table_name} '
                    f'response: {response}'
                )
            except ClientError as e:
                log.error(
                    f'Failed revoking principal {principal} '
                    f'Table permissions {permissions}'
                    f'to {catalog_id}://{database_name}/{table_name} '
                    f'due to: {e}'
                )
                raise e

    def revoke_permissions_from_table_with_columns(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None
    ):
        for principal in principals:
            try:
                revoke_dict = dict(
                    Id=str(uuid.uuid4()),
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'TableWithColumns': {
                            'DatabaseName': database_name,
                            'Name': table_name,
                            'ColumnWildcard': {},
                            'CatalogId': catalog_id,
                        }
                    },
                    Permissions=permissions,
                )
                if permissions_with_grant_options:
                    revoke_dict[
                        'PermissionsWithGrantOption'
                    ] = permissions_with_grant_options

                response = self._client.revoke_permissions(**revoke_dict)
                log.info(
                    f'Successfully revoked principal {principal} '
                    f'TableWithColumns permissions {permissions} '
                    f'to {catalog_id}://{database_name}/{table_name} '
                    f'response: {response}'
                )
            except ClientError as e:
                log.error(
                    f'Failed revoking principal {principal} '
                    f'TableWithColumns permissions {permissions}'
                    f'to {catalog_id}://{database_name}/{table_name} '
                    f'due to: {e}'
                )
                raise e
