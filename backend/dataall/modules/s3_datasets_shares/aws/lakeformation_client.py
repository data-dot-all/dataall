import logging
from typing import List
import time

from botocore.exceptions import ClientError
from retrying import Retrying

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger('aws:lakeformation')


class LakeFormationClient:
    def __init__(self, account_id, region):
        self._session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = self._session.client('lakeformation', region_name=region)

    def upgrade_lakeformation_data_catalog_settings(self, version_num=3):
        """
        Upgrades the AWS Lake Formation data catalog settings version.

        Returns:
        None
        """
        try:
            # Get the current Lake Formation settings
            settings = self._client.get_data_lake_settings()['DataLakeSettings']
            # Check if the current version is already 3
            if int(settings['Parameters']['CROSS_ACCOUNT_VERSION']) >= version_num:
                log.info(f'Lake Formation settings are already at Version {str(version_num)}.')
                return

            settings['Parameters']['CROSS_ACCOUNT_VERSION'] = str(version_num)
            # Update the settings to Version 3
            self._client.put_data_lake_settings(
                DataLakeSettings={
                    **settings,
                }
            )

            log.info(f'Lake Formation settings have been upgraded to Version {str(version_num)}.')

        except Exception as e:
            print(f'Error upgrading Lake Formation settings to Version {str(version_num)}: {e}')

    def grant_permissions_to_database(
        self,
        principals,
        database_name,
        permissions,
    ) -> True:
        resource = {
            'Database': {'Name': database_name},
        }
        self._grant_permissions_to_resource(principals=principals, resource=resource, permissions=permissions)
        return True

    def grant_permissions_to_table(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None,
    ) -> True:
        resource = {
            'Table': {
                'DatabaseName': database_name,
                'Name': table_name,
                'CatalogId': catalog_id,
            }
        }
        self._grant_permissions_to_resource(
            principals=principals,
            resource=resource,
            permissions=permissions,
            permissions_with_grant_options=permissions_with_grant_options,
        )
        return True

    def grant_permissions_to_table_with_columns(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None,
    ) -> True:
        resource = {
            'TableWithColumns': {
                'DatabaseName': database_name,
                'Name': table_name,
                'ColumnWildcard': {},
                'CatalogId': catalog_id,
            }
        }
        check_resource = {
            'Table': {
                'DatabaseName': database_name,
                'Name': table_name,
                'CatalogId': catalog_id,
            }
        }
        self._grant_permissions_to_resource(
            principals=principals,
            resource=resource,
            permissions=permissions,
            permissions_with_grant_options=permissions_with_grant_options,
            check_resource=check_resource,
        )
        return True

    def grant_permissions_to_table_with_filters(
        self, principals, database_name, table_name, catalog_id, permissions, data_filters=[]
    ) -> True:
        for f_name in data_filters:
            data_filter_resource = {
                'DataCellsFilter': {
                    'TableCatalogId': catalog_id,
                    'DatabaseName': database_name,
                    'TableName': table_name,
                    'Name': f_name,
                },
            }
            self._grant_permissions_to_resource(
                principals=principals,
                resource=data_filter_resource,
                permissions=permissions,
                permissions_with_grant_options=None,
                check_resource=data_filter_resource,
            )
        return True

    def _grant_permissions_to_resource(
        self,
        principals: List,
        resource: dict,
        permissions: List,
        permissions_with_grant_options: List = None,
        check_resource: dict = None,
    ) -> True:
        for principal in principals:
            try:
                if not self._check_permissions_to_resource(
                    principal=principal,
                    resource=resource,
                    permissions=permissions,
                    permissions_with_grant_options=permissions_with_grant_options,
                    check_resource=check_resource,
                ):
                    log.info(f'Granting principal {principal} permissions {permissions} to {str(resource)}...')
                    # We define the grant with "permissions" instead of "missing_permissions" because we want to avoid
                    # duplicates done by data.all, but we want to avoid dependencies with external grants
                    grant_dict = dict(
                        Principal={'DataLakePrincipalIdentifier': principal},
                        Resource=resource,
                        Permissions=permissions,
                    )
                    if permissions_with_grant_options:
                        grant_dict['PermissionsWithGrantOption'] = permissions_with_grant_options

                    response = Retrying(
                        retry_on_exception=lambda ex: isinstance(
                            ex, self._client.exceptions.ConcurrentModificationException
                        ),
                        stop_max_attempt_number=5,
                        wait_random_min=1000,
                        wait_random_max=3000,
                    ).call(self._client.grant_permissions, **grant_dict)

                    log.info(
                        f'Successfully granted principal {principal} '
                        f'permissions {permissions} '
                        f'and permissions with grant options {permissions_with_grant_options} '
                        f'to {str(resource)}  '
                        f'response: {response}'
                    )
                    time.sleep(2)

            except ClientError as e:
                log.error(
                    f'Could not grant principal {principal} '
                    f'permissions {permissions} '
                    f'and permissions with grant options {permissions_with_grant_options} '
                    f'to {str(resource)}  '
                    f'due to: {e}'
                )
                raise e
        return True

    def revoke_permissions_to_database(
        self,
        principals,
        database_name,
        permissions,
    ) -> True:
        resource = {
            'Database': {'Name': database_name},
        }
        self._revoke_permissions_from_resource(principals=principals, resource=resource, permissions=permissions)
        return True

    def revoke_permissions_from_table(
        self, principals, database_name, table_name, catalog_id, permissions, permissions_with_grant_options=None
    ) -> True:
        resource = {
            'Table': {
                'DatabaseName': database_name,
                'Name': table_name,
                'CatalogId': catalog_id,
            }
        }
        self._revoke_permissions_from_resource(
            principals=principals,
            resource=resource,
            permissions=permissions,
            permissions_with_grant_options=permissions_with_grant_options,
        )
        return True

    def revoke_permissions_from_table_with_columns(
        self, principals, database_name, table_name, catalog_id, permissions, permissions_with_grant_options=None
    ) -> True:
        resource = {
            'TableWithColumns': {
                'DatabaseName': database_name,
                'Name': table_name,
                'ColumnWildcard': {},
                'CatalogId': catalog_id,
            }
        }
        self._revoke_permissions_from_resource(
            principals=principals,
            resource=resource,
            permissions=permissions,
            permissions_with_grant_options=permissions_with_grant_options,
        )
        return True

    def revoke_permissions_to_table_with_filters(
        self, principals, database_name, table_name, catalog_id, permissions, data_filters
    ) -> True:
        for f_name in data_filters:
            data_filter_resource = {
                'DataCellsFilter': {
                    'TableCatalogId': catalog_id,
                    'DatabaseName': database_name,
                    'TableName': table_name,
                    'Name': f_name,
                },
            }
            self._revoke_permissions_from_resource(
                principals=principals,
                resource=data_filter_resource,
                permissions=permissions,
            )
        return True

    def _revoke_permissions_from_resource(
        self, principals, resource, permissions, permissions_with_grant_options=None
    ) -> True:
        for principal in principals:
            try:
                log.info(
                    f'Revoking principal {principal} '
                    f'permissions {permissions} '
                    f'and permissions with grant options {permissions_with_grant_options} '
                    f'to {str(resource)}... '
                )
                revoke_dict = dict(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource=resource,
                    Permissions=permissions,
                )
                if permissions_with_grant_options:
                    revoke_dict['PermissionsWithGrantOption'] = permissions_with_grant_options

                response = self._client.revoke_permissions(**revoke_dict)
                log.info(
                    f'Successfully revoked principal {principal} '
                    f'permissions {permissions} '
                    f'and permissions with grant options {permissions_with_grant_options} '
                    f'to {str(resource)} '
                    f'response: {response}'
                )
                time.sleep(2)
            except ClientError as error:
                response = error.response
                if not (
                    response['Error']['Code'] == 'InvalidInputException'
                    and (
                        'Grantee has no permissions' in response['Error']['Message']
                        or 'No permissions revoked' in response['Error']['Message']
                        or 'not found' in response['Error']['Message']
                    )
                ):
                    log.error(
                        f'Failed revoking principal {principal} '
                        f'permissions {permissions} '
                        f'and permissions with grant options {permissions_with_grant_options} '
                        f'to {str(resource)} '
                        f'due to: {error}'
                    )
                    raise error
                log.warning(
                    f'Principal {principal} already has revoked'
                    f'permissions {permissions} '
                    f'and permissions with grant options {permissions_with_grant_options} '
                    f'to {str(resource)} '
                    f'response error: {error}'
                )
        return True

    def check_permissions_to_database(
        self,
        principals,
        database_name,
        permissions,
    ) -> True:
        resource = {
            'Database': {'Name': database_name},
        }
        check = []
        for principal in principals:
            check.append(
                self._check_permissions_to_resource(principal=principal, resource=resource, permissions=permissions)
            )
        return all(check)

    def check_permissions_to_table(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None,
    ) -> True:
        resource = {
            'Table': {
                'DatabaseName': database_name,
                'Name': table_name,
                'CatalogId': catalog_id,
            }
        }
        check = []
        for principal in principals:
            check.append(
                self._check_permissions_to_resource(
                    principal=principal,
                    resource=resource,
                    permissions=permissions,
                    permissions_with_grant_options=permissions_with_grant_options,
                )
            )
        return all(check)

    def check_permissions_to_table_with_columns(
        self,
        principals,
        database_name,
        table_name,
        catalog_id,
        permissions,
        permissions_with_grant_options=None,
    ) -> True:
        resource = {
            'TableWithColumns': {
                'DatabaseName': database_name,
                'Name': table_name,
                'ColumnWildcard': {},
                'CatalogId': catalog_id,
            }
        }
        check_resource = {
            'Table': {
                'DatabaseName': database_name,
                'Name': table_name,
                'CatalogId': catalog_id,
            }
        }
        check = []
        for principal in principals:
            check.append(
                self._check_permissions_to_resource(
                    principal=principal,
                    resource=resource,
                    permissions=permissions,
                    permissions_with_grant_options=permissions_with_grant_options,
                    check_resource=check_resource,
                )
            )
        return all(check)

    def check_permissions_to_table_with_filters(
        self, principals, database_name, table_name, catalog_id, permissions, data_filters=[]
    ) -> True:
        check = []
        for principal in principals:
            for f_name in data_filters:
                data_filter_resource = {
                    'DataCellsFilter': {
                        'TableCatalogId': catalog_id,
                        'DatabaseName': database_name,
                        'TableName': table_name,
                        'Name': f_name,
                    },
                }
                check.append(
                    self._check_permissions_to_resource(
                        principal=principal,
                        resource=data_filter_resource,
                        permissions=permissions,
                        permissions_with_grant_options=None,
                        check_resource=data_filter_resource,
                    )
                )
        return all(check)

    def _check_permissions_to_resource(
        self,
        principal: str,
        resource: dict,
        permissions: List,
        permissions_with_grant_options: List = None,
        check_resource: dict = None,
    ) -> bool:
        try:
            log.info(f'Checking principal {principal} permissions {permissions} to {str(resource)}...')
            check_dict = dict(
                Principal={'DataLakePrincipalIdentifier': principal},
                Resource=check_resource if check_resource else resource,
            )

            # Cannot Specify Filter by Principal for Data Filter List Permissions
            if 'DataCellsFilter' in check_dict['Resource']:
                del check_dict['Principal']

            existing = self._client.list_permissions(**check_dict)
            current = []
            current_grant = []
            for permission in existing['PrincipalResourcePermissions']:
                if permission['Principal']['DataLakePrincipalIdentifier'] == principal:
                    current.extend(permission['Permissions'])
                    current_grant.extend(permission['PermissionsWithGrantOption'])

            missing_permissions = list(set(permissions) - set(current))
            missing_grant_permissions = (
                list(set(permissions_with_grant_options) - set(current_grant)) if permissions_with_grant_options else []
            )

            if missing_permissions or missing_grant_permissions:
                return False
            else:
                log.info(
                    f'Already granted principal {principal} '
                    f'permissions {permissions} '
                    f'and permissions with grant options {permissions_with_grant_options} '
                    f'to {str(resource)}  '
                    f'response: {existing}'
                )
                return True
        except ClientError as e:
            log.error(f'Could not list principal {principal} permissions {permissions} to {str(resource)}  due to: {e}')
            raise e
