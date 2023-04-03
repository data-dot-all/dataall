import logging
import re
import os
import ast

from botocore.exceptions import ClientError
from .sts import SessionHelper
from .secrets_manager import SecretsManager
from .parameter_store import ParameterStoreManager

logger = logging.getLogger('QuicksightHandler')
logger.setLevel(logging.DEBUG)

DEFAULT_GROUP_NAME = 'dataall'


class Quicksight:
    def __init__(self):
        pass

    @staticmethod
    def get_quicksight_client(AwsAccountId, region='eu-west-1'):
        """Returns a boto3 quicksight client in the provided account/region
        Args:
            AwsAccountId(str) : aws account id
            region(str) : aws region
        Returns : boto3.client ("quicksight")
        """
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('quicksight', region_name=region)

    @staticmethod
    def get_identity_region(AwsAccountId):
        """Quicksight manages identities in one region, and there is no API to retrieve it
        However, when using Quicksight user/group apis in the wrong region,
        the client will throw and exception showing the region Quicksight's using as its
        identity region.
        Args:
            AwsAccountId(str) : aws account id
        Returns: str
            the region quicksight uses as identity region
        """
        identity_region_rex = re.compile('Please use the (?P<region>.*) endpoint.')
        identity_region = 'us-east-1'
        client = Quicksight.get_quicksight_client(AwsAccountId=AwsAccountId, region=identity_region)
        try:
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName=DEFAULT_GROUP_NAME, Namespace='default'
            )
        except client.exceptions.AccessDeniedException as e:
            match = identity_region_rex.findall(str(e))
            if match:
                identity_region = match[0]
            else:
                raise e
        except client.exceptions.ResourceNotFoundException:
            pass
        return identity_region

    @staticmethod
    def get_quicksight_client_in_identity_region(AwsAccountId):
        """Returns a boto3 quicksight client in the Quicksight identity region for the provided account
        Args:
            AwsAccountId(str) : aws account id
        Returns : boto3.client ("quicksight")

        """
        identity_region = Quicksight.get_identity_region(AwsAccountId)
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('quicksight', region_name=identity_region)

    @staticmethod
    def check_quicksight_enterprise_subscription(AwsAccountId):
        """Use the DescribeAccountSubscription operation to receive a description of a Amazon QuickSight account's subscription. A successful API call returns an AccountInfo object that includes an account's name, subscription status, authentication type, edition, and notification email address.
        Args:
            AwsAccountId(str) : aws account id
        Returns: bool
            True if Quicksight Enterprise Edition is enabled in the AWS Account
        """
        client = Quicksight.get_quicksight_client(AwsAccountId=AwsAccountId)
        try:
            response = client.describe_account_subscription(AwsAccountId=AwsAccountId)
            if not response['AccountInfo']:
                raise Exception(f'Quicksight Enterprise Subscription not found in Account: {AwsAccountId}')
            else:
                if response['AccountInfo']['Edition'] not in ['ENTERPRISE', 'ENTERPRISE_AND_Q']:
                    raise Exception(
                        f"Quicksight Subscription found in Account: {AwsAccountId} of incorrect type: {response['AccountInfo']['Edition']}")
                else:
                    if response['AccountInfo']['AccountSubscriptionStatus'] == 'ACCOUNT_CREATED':
                        return True
                    else:
                        raise Exception(
                            f"Quicksight Subscription found in Account: {AwsAccountId} not active. Status = {response['AccountInfo']['AccountSubscriptionStatus']}")

        except client.exceptions.ResourceNotFoundException:
            raise Exception('Quicksight Enterprise Subscription not found')

        except client.exceptions.AccessDeniedException:
            raise Exception('Access denied to Quicksight for data.all PivotRole')

    @staticmethod
    def create_quicksight_group(AwsAccountId, GroupName=DEFAULT_GROUP_NAME):
        """Creates a Quicksight group called GroupName
        Args:
            AwsAccountId(str):  aws account
            GroupName(str): name of the QS group

        Returns:dict
            quicksight.describe_group response
        """
        client = Quicksight.get_quicksight_client_in_identity_region(AwsAccountId)
        group = Quicksight.describe_group(client, AwsAccountId, GroupName)

        if not group:
            logger.info(f'Attempting to create Quicksight group `{GroupName}...')
            response = client.create_group(
                GroupName=GroupName,
                Description='data.all group',
                AwsAccountId=AwsAccountId,
                Namespace='default',
            )
            logger.info(f'Quicksight group {GroupName} created {response}')
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName=GroupName, Namespace='default'
            )
            return response
        return group

    @staticmethod
    def describe_group(client, AwsAccountId, GroupName=DEFAULT_GROUP_NAME):
        try:
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName=GroupName, Namespace='default'
            )
            logger.info(
                f'Quicksight {GroupName} group already exists in {AwsAccountId} '
                f'(using identity region {Quicksight.get_identity_region(AwsAccountId)}): '
                f'{response}'
            )
            return response
        except client.exceptions.ResourceNotFoundException:
            logger.info(
                f'Creating Quicksight group in {AwsAccountId} (using identity region {Quicksight.get_identity_region(AwsAccountId)})'
            )

    @staticmethod
    def describe_user(AwsAccountId, UserName):
        """Describes a QS user, returns None if not found
        Args:
            AwsAccountId(str) : aws account
            UserName(str) : name of the QS user
        """
        client = Quicksight.get_quicksight_client_in_identity_region(AwsAccountId)
        try:
            response = client.describe_user(
                UserName=UserName, AwsAccountId=AwsAccountId, Namespace='default'
            )
            exists = True
        except ClientError:
            return None
        return response.get('User')

    @staticmethod
    def get_quicksight_group_arn(AwsAccountId):
        default_group_arn = None
        group = Quicksight.describe_group(
            client=Quicksight.get_quicksight_client_in_identity_region(
                AwsAccountId=AwsAccountId
            ),
            AwsAccountId=AwsAccountId,
        )
        if group and group.get('Group', {}).get('Arn'):
            default_group_arn = group.get('Group', {}).get('Arn')

        return default_group_arn

    @staticmethod
    def list_user_groups(AwsAccountId, UserName):
        client = Quicksight.get_quicksight_client_in_identity_region(AwsAccountId)
        user = Quicksight.describe_user(AwsAccountId, UserName)
        if not user:
            return []
        response = client.list_user_groups(
            UserName=UserName, AwsAccountId=AwsAccountId, Namespace='default'
        )
        return response['GroupList']

    @staticmethod
    def register_user_in_group(AwsAccountId, UserName, GroupName, UserRole='READER'):
        client = Quicksight.get_quicksight_client_in_identity_region(
            AwsAccountId=AwsAccountId
        )
        exists = False
        user = Quicksight.describe_user(AwsAccountId, UserName=UserName)

        if user is not None:
            exists = True

        if exists:
            response = client.update_user(
                UserName=UserName,
                AwsAccountId=AwsAccountId,
                Namespace='default',
                Email=UserName,
                Role=UserRole,
            )
        else:
            response = client.register_user(
                UserName=UserName,
                Email=UserName,
                AwsAccountId=AwsAccountId,
                Namespace='default',
                IdentityType='QUICKSIGHT',
                UserRole=UserRole,
            )
        member = False

        Quicksight.create_quicksight_group(AwsAccountId, GroupName)
        response = client.list_user_groups(
            UserName=UserName, AwsAccountId=AwsAccountId, Namespace='default'
        )
        logger.info(
            f'list_user_groups for {UserName}: {response})'
        )
        if GroupName not in [g['GroupName'] for g in response['GroupList']]:
            logger.warning(f'Adding {UserName} to Quicksight group {GroupName} on {AwsAccountId}')
            response = client.create_group_membership(
                MemberName=UserName,
                GroupName=GroupName,
                AwsAccountId=AwsAccountId,
                Namespace='default',
            )
        return Quicksight.describe_user(AwsAccountId, UserName)

    @staticmethod
    def get_reader_session(
        AwsAccountId, region, UserName, UserRole='READER', DashboardId=None
    ):

        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        user = Quicksight.describe_user(AwsAccountId, UserName)
        if user is None:
            user = Quicksight.register_user_in_group(
                AwsAccountId=AwsAccountId, UserName=UserName, GroupName=DEFAULT_GROUP_NAME, UserRole=UserRole
            )

        response = client.get_dashboard_embed_url(
            AwsAccountId=AwsAccountId,
            DashboardId=DashboardId,
            IdentityType='QUICKSIGHT',
            SessionLifetimeInMinutes=120,
            UserArn=user.get('Arn'),
        )
        return response.get('EmbedUrl')

    @staticmethod
    def check_dashboard_permissions(AwsAccountId, region, DashboardId):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        response = client.describe_dashboard_permissions(
            AwsAccountId=AwsAccountId,
            DashboardId=DashboardId
        )['Permissions']
        logger.info(f"Dashboard initial permissions: {response}")
        read_principals = []
        write_principals = []

        for a, p in zip([p["Actions"] for p in response], [p["Principal"] for p in response]):
            write_principals.append(p) if "Update" in str(a) else read_principals.append(p)

        logger.info(f"Dashboard updated permissions, Read principals: {read_principals}")
        logger.info(f"Dashboard updated permissions, Write principals: {write_principals}")

        return read_principals, write_principals

    @staticmethod
    def get_shared_reader_session(
            AwsAccountId, region, UserName, GroupName, UserRole='READER', DashboardId=None
    ):

        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        identity_region = Quicksight.get_identity_region(AwsAccountId)
        groupPrincipal = f"arn:aws:quicksight:{identity_region}:{AwsAccountId}:group/default/{GroupName}"

        user = Quicksight.register_user_in_group(
            AwsAccountId=AwsAccountId, UserName=UserName, GroupName=GroupName, UserRole=UserRole
        )

        read_principals, write_principals = Quicksight.check_dashboard_permissions(
            AwsAccountId=AwsAccountId,
            region=region,
            DashboardId=DashboardId
        )

        if groupPrincipal not in read_principals:
            permissions = client.update_dashboard_permissions(
                AwsAccountId=AwsAccountId,
                DashboardId=DashboardId,
                GrantPermissions=[
                    {
                        'Principal': groupPrincipal,
                        'Actions': [
                            "quicksight:DescribeDashboard",
                            "quicksight:ListDashboardVersions",
                            "quicksight:QueryDashboard",
                        ]
                    },
                ]
            )
            logger.info(f"Permissions granted: {permissions}")

        response = client.get_dashboard_embed_url(
            AwsAccountId=AwsAccountId,
            DashboardId=DashboardId,
            IdentityType='QUICKSIGHT',
            SessionLifetimeInMinutes=120,
            UserArn=user.get('Arn'),
        )
        return response.get('EmbedUrl')

    @staticmethod
    def get_anonymous_session(AwsAccountId, region, UserName, DashboardId=None):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        response = client.generate_embed_url_for_anonymous_user(
            AwsAccountId=AwsAccountId,
            SessionLifetimeInMinutes=120,
            Namespace='default',
            SessionTags=[
                {'Key': DEFAULT_GROUP_NAME, 'Value': UserName},
            ],
            AuthorizedResourceArns=[
                f'arn:aws:quicksight:{region}:{AwsAccountId}:dashboard/{DashboardId}',
            ],
            ExperienceConfiguration={'Dashboard': {'InitialDashboardId': DashboardId}},
        )
        return response.get('EmbedUrl')

    @staticmethod
    def get_author_session(AwsAccountId, region, UserName, UserRole='AUTHOR'):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        user = Quicksight.describe_user(AwsAccountId, UserName=UserName)
        if user is None:
            user = Quicksight.register_user_in_group(
                AwsAccountId=AwsAccountId, UserName=UserName, GroupName=DEFAULT_GROUP_NAME, UserRole=UserRole
            )
        elif user.get("Role", None) not in ["AUTHOR", "ADMIN"]:
            user = Quicksight.register_user_in_group(
                AwsAccountId=AwsAccountId, UserName=UserName, GroupName=DEFAULT_GROUP_NAME, UserRole=UserRole
            )
        else:
            pass
        response = client.get_session_embed_url(
            AwsAccountId=AwsAccountId,
            EntryPoint='/start/dashboards',
            SessionLifetimeInMinutes=120,
            UserArn=user['Arn'],
        )
        return response['EmbedUrl']

    @staticmethod
    def can_import_dashboard(AwsAccountId, region, UserName, DashboardId):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        user = Quicksight.describe_user(AwsAccountId, UserName)
        if not user:
            return False

        groups = Quicksight.list_user_groups(AwsAccountId, UserName)
        grouparns = [g['Arn'] for g in groups]
        try:
            response = client.describe_dashboard_permissions(
                AwsAccountId=AwsAccountId, DashboardId=DashboardId
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

    @staticmethod
    def create_data_source_vpc(AwsAccountId, region, UserName, vpcConnectionId):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        identity_region = 'us-east-1'
        user = Quicksight.register_user_in_group(
            AwsAccountId=AwsAccountId, UserName=UserName, GroupName=DEFAULT_GROUP_NAME, UserRole='AUTHOR'
        )
        try:
            response = client.describe_data_source(
                AwsAccountId=AwsAccountId, DataSourceId="dataall-metadata-db"
            )

        except client.exceptions.ResourceNotFoundException:
            aurora_secret_arn = ParameterStoreManager.get_parameter_value(AwsAccountId=AwsAccountId, region=region, parameter_path=f'/dataall/{os.getenv("envname", "local")}/aurora/secret_arn')
            aurora_params = SecretsManager.get_secret_value(
                AwsAccountId=AwsAccountId, region=region, secretId=aurora_secret_arn
            )
            aurora_params_dict = ast.literal_eval(aurora_params)
            response = client.create_data_source(
                AwsAccountId=AwsAccountId,
                DataSourceId="dataall-metadata-db",
                Name="dataall-metadata-db",
                Type="AURORA_POSTGRESQL",
                DataSourceParameters={
                    'AuroraPostgreSqlParameters': {
                        'Host': aurora_params_dict["host"],
                        'Port': aurora_params_dict["port"],
                        'Database': aurora_params_dict["dbname"]
                    }
                },
                Credentials={
                    "CredentialPair": {
                        "Username": aurora_params_dict["username"],
                        "Password": aurora_params_dict["password"],
                    }
                },
                Permissions=[
                    {
                        "Principal": f"arn:aws:quicksight:{region}:{AwsAccountId}:group/default/dataall",
                        "Actions": [
                            "quicksight:UpdateDataSourcePermissions",
                            "quicksight:DescribeDataSource",
                            "quicksight:DescribeDataSourcePermissions",
                            "quicksight:PassDataSource",
                            "quicksight:UpdateDataSource",
                            "quicksight:DeleteDataSource"
                        ]
                    }
                ],
                VpcConnectionProperties={
                    'VpcConnectionArn': f"arn:aws:quicksight:{region}:{AwsAccountId}:vpcConnection/{vpcConnectionId}"
                }
            )

        return "dataall-metadata-db"

    @staticmethod
    def create_data_set_from_source(AwsAccountId, region, UserName, dataSourceId, tablesToImport):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        user = Quicksight.describe_user(AwsAccountId, UserName)
        if not user:
            return False

        data_source = client.describe_data_source(
            AwsAccountId=AwsAccountId,
            DataSourceId=dataSourceId
        )

        if not data_source:
            return False

        for table in tablesToImport:

            response = client.create_data_set(
                AwsAccountId=AwsAccountId,
                DataSetId=f"dataall-imported-{table}",
                Name=f"dataall-imported-{table}",
                PhysicalTableMap={
                    'string': {
                        'RelationalTable': {
                            'DataSourceArn': data_source.get('DataSource').get('Arn'),
                            'Catalog': 'string',
                            'Schema': 'dev',
                            'Name': table,
                            'InputColumns': [
                                {
                                    'Name': 'string',
                                    'Type': 'STRING'
                                },
                            ]
                        }
                    }},
                ImportMode='DIRECT_QUERY',
                Permissions=[
                    {
                        'Principal': user.get('Arn'),
                        'Actions': [
                            "quicksight:DescribeDataSet",
                            "quicksight:DescribeDataSetPermissions",
                            "quicksight:PassDataSet",
                            "quicksight:DescribeIngestion",
                            "quicksight:ListIngestions"
                        ]
                    },
                ],
            )

        return True

    @staticmethod
    def create_analysis(AwsAccountId, region, UserName):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        user = Quicksight.describe_user(AwsAccountId, UserName)
        if not user:
            return False

        response = client.create_analysis(
            AwsAccountId=AwsAccountId,
            AnalysisId='dataallMonitoringAnalysis',
            Name='dataallMonitoringAnalysis',
            Permissions=[
                {
                    'Principal': user.get('Arn'),
                    'Actions': [
                        'quicksight:DescribeAnalysis',
                        'quicksight:DescribeAnalysisPermissions',
                        'quicksight:UpdateAnalysisPermissions',
                        'quicksight:UpdateAnalysis'
                    ]
                },
            ],
            SourceEntity={
                'SourceTemplate': {
                    'DataSetReferences': [
                        {
                            'DataSetPlaceholder': 'environment',
                            'DataSetArn': f"arn:aws:quicksight:{region}:{AwsAccountId}:dataset/<DATASET-ID>"
                        },
                    ],
                    'Arn': '<TEMPLATE-THAT-WE-WANT-TO-MIGRATE'
                }
            },
            Tags=[
                {
                    'Key': 'application',
                    'Value': 'dataall'
                },
            ]
        )

        return True
