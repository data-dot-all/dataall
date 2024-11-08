import logging
import os
import ast

from botocore.exceptions import ClientError

from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.aws.quicksight import QuicksightClient
from dataall.base.aws.secrets_manager import SecretsManager

log = logging.getLogger(__name__)


class DashboardQuicksightClient:
    _DEFAULT_GROUP_NAME = QuicksightClient.DEFAULT_GROUP_NAME

    def __init__(self, username, aws_account_id, region='eu-west-1'):
        self._account_id = aws_account_id
        self._region = region
        self._username = username
        self._client = QuicksightClient.get_quicksight_client(
            AwsAccountId=aws_account_id, region=region, session_region=region
        )

    def register_user_in_group(self, group_name, user_role='READER'):
        identity_region_client = QuicksightClient.get_quicksight_client_in_identity_region(
            self._account_id, self._region
        )
        QuicksightClient.create_quicksight_group(
            AwsAccountId=self._account_id, region=self._region, GroupName=group_name
        )
        user = self._describe_user()

        if user is not None:
            identity_region_client.update_user(
                UserName=self._username,
                AwsAccountId=self._account_id,
                Namespace='default',
                Email=self._username,
                Role=user_role,
            )
        else:
            identity_region_client.register_user(
                UserName=self._username,
                Email=self._username,
                AwsAccountId=self._account_id,
                Namespace='default',
                IdentityType='QUICKSIGHT',
                UserRole=user_role,
            )

        response = identity_region_client.list_user_groups(
            UserName=self._username, AwsAccountId=self._account_id, Namespace='default'
        )
        log.info(f'list_user_groups for {self._username}: {response})')
        if group_name not in [g['GroupName'] for g in response['GroupList']]:
            log.warning(f'Adding {self._username} to Quicksight group {group_name} on {self._account_id}')
            identity_region_client.create_group_membership(
                MemberName=self._username,
                GroupName=group_name,
                AwsAccountId=self._account_id,
                Namespace='default',
            )
        return self._describe_user()

    def get_reader_session(self, user_role='READER', dashboard_id=None, domain_name: str = None):
        user = self._describe_user()
        if user is None:
            user = self.register_user_in_group(self._DEFAULT_GROUP_NAME, user_role)

        response = self._client.generate_embed_url_for_registered_user(
            AwsAccountId=self._account_id,
            SessionLifetimeInMinutes=120,
            UserArn=user.get('Arn'),
            ExperienceConfiguration={
                'Dashboard': {
                    'InitialDashboardId': dashboard_id,
                },
            },
            AllowedDomains=[domain_name],
        )
        return response.get('EmbedUrl')

    def get_shared_reader_session(self, group_name, user_role='READER', dashboard_id=None):
        aws_account_id = self._account_id
        identity_region = QuicksightClient.get_identity_region(aws_account_id, self._region)
        group_principal = f'arn:aws:quicksight:{identity_region}:{aws_account_id}:group/default/{group_name}'

        user = self.register_user_in_group(group_name, user_role)

        read_principals, write_principals = self._check_dashboard_permissions(dashboard_id)

        if group_principal not in read_principals:
            permissions = self._client.update_dashboard_permissions(
                AwsAccountId=aws_account_id,
                DashboardId=dashboard_id,
                GrantPermissions=[
                    {
                        'Principal': group_principal,
                        'Actions': [
                            'quicksight:DescribeDashboard',
                            'quicksight:ListDashboardVersions',
                            'quicksight:QueryDashboard',
                        ],
                    },
                ],
            )
            log.info(f'Permissions granted: {permissions}')

        response = self._client.get_dashboard_embed_url(
            AwsAccountId=aws_account_id,
            DashboardId=dashboard_id,
            IdentityType='QUICKSIGHT',
            SessionLifetimeInMinutes=120,
            UserArn=user.get('Arn'),
        )
        return response.get('EmbedUrl')

    def get_anonymous_session(self, dashboard_id=None):
        response = self._client.generate_embed_url_for_anonymous_user(
            AwsAccountId=self._account_id,
            SessionLifetimeInMinutes=120,
            Namespace='default',
            SessionTags=[{'Key': self._DEFAULT_GROUP_NAME, 'Value': self._username}],
            AuthorizedResourceArns=[
                f'arn:aws:quicksight:{self._region}:{self._account_id}:dashboard/{dashboard_id}',
            ],
            ExperienceConfiguration={'Dashboard': {'InitialDashboardId': dashboard_id}},
        )
        return response.get('EmbedUrl')

    def get_author_session(self):
        user = self._describe_user()
        if user is None or user.get('Role', None) not in ['AUTHOR', 'ADMIN']:
            user = self.register_user_in_group(self._DEFAULT_GROUP_NAME, 'AUTHOR')

        response = self._client.get_session_embed_url(
            AwsAccountId=self._account_id,
            EntryPoint='/start/dashboards',
            SessionLifetimeInMinutes=120,
            UserArn=user['Arn'],
        )
        return response['EmbedUrl']

    def can_import_dashboard(self, dashboard_id):
        user = self._describe_user()
        if not user:
            return False

        groups = self._list_user_groups()
        grouparns = [g['Arn'] for g in groups]
        try:
            response = self._client.describe_dashboard_permissions(
                AwsAccountId=self._account_id, DashboardId=dashboard_id
            )
        except ClientError as e:
            raise e

        permissions = response.get('Permissions', [])
        for p in permissions:
            if p['Principal'] == user.get('Arn') or p['Principal'] in grouparns:
                for a in p['Actions']:
                    if a in [
                        'quicksight:UpdateDashboard',
                        'UpdateDashboardPermissions',
                    ]:
                        return True

        return False

    def create_data_source_vpc(self, vpc_connection_id):
        client = self._client
        aws_account_id = self._account_id
        region = self._region

        self.register_user_in_group(self._DEFAULT_GROUP_NAME, 'AUTHOR')
        try:
            client.describe_data_source(AwsAccountId=aws_account_id, DataSourceId='dataall-metadata-db')

        except client.exceptions.ResourceNotFoundException:
            aurora_secret_arn = ParameterStoreManager.get_parameter_value(
                AwsAccountId=aws_account_id,
                region=region,
                parameter_path=f'/dataall/{os.getenv("envname", "local")}/aurora/secret_arn',
            )

            aurora_params = SecretsManager(aws_account_id, region).get_secret_value(secret_id=aurora_secret_arn)
            aurora_params_dict = ast.literal_eval(aurora_params)
            client.create_data_source(
                AwsAccountId=aws_account_id,
                DataSourceId='dataall-metadata-db',
                Name='dataall-metadata-db',
                Type='AURORA_POSTGRESQL',
                DataSourceParameters={
                    'AuroraPostgreSqlParameters': {
                        'Host': aurora_params_dict['host'],
                        'Port': '5432',
                        'Database': aurora_params_dict['dbname'],
                    }
                },
                Credentials={
                    'CredentialPair': {
                        'Username': aurora_params_dict['username'],
                        'Password': aurora_params_dict['password'],
                    }
                },
                Permissions=[
                    {
                        'Principal': f'arn:aws:quicksight:{region}:{aws_account_id}:group/default/dataall',
                        'Actions': [
                            'quicksight:UpdateDataSourcePermissions',
                            'quicksight:DescribeDataSource',
                            'quicksight:DescribeDataSourcePermissions',
                            'quicksight:PassDataSource',
                            'quicksight:UpdateDataSource',
                            'quicksight:DeleteDataSource',
                        ],
                    }
                ],
                VpcConnectionProperties={
                    'VpcConnectionArn': f'arn:aws:quicksight:{region}:{aws_account_id}:vpcConnection/'
                    f'{vpc_connection_id}'
                },
            )

        return 'dataall-metadata-db'

    def _check_dashboard_permissions(self, dashboard_id):
        response = self._client.describe_dashboard_permissions(AwsAccountId=self._account_id, DashboardId=dashboard_id)[
            'Permissions'
        ]
        log.info(f'Dashboard initial permissions: {response}')
        read_principals = []
        write_principals = []

        for a, p in zip([p['Actions'] for p in response], [p['Principal'] for p in response]):
            write_principals.append(p) if 'Update' in str(a) else read_principals.append(p)

        log.info(f'Dashboard updated permissions, Read principals: {read_principals}')
        log.info(f'Dashboard updated permissions, Write principals: {write_principals}')

        return read_principals, write_principals

    def _list_user_groups(self):
        client = QuicksightClient.get_quicksight_client_in_identity_region(self._account_id, self._region)
        user = self._describe_user()
        if not user:
            return []
        response = client.list_user_groups(UserName=self._username, AwsAccountId=self._account_id, Namespace='default')
        return response['GroupList']

    def _describe_user(self):
        """Describes a QS user, returns None if not found"""
        client = QuicksightClient.get_quicksight_client_in_identity_region(self._account_id, self._region)
        try:
            response = client.describe_user(UserName=self._username, AwsAccountId=self._account_id, Namespace='default')
        except ClientError:
            return None
        return response.get('User')
