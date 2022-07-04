import logging
import re

from botocore.exceptions import ClientError

from .sts import SessionHelper
from .secrets_manager import SecretsManager

logger = logging.getLogger('QuicksightHandler')
logger.setLevel(logging.DEBUG)


class Quicksight:
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
        session = SessionHelper.remote_session(AwsAccountId)
        identity_region = 'us-east-1'
        client = session.client('quicksight', region_name=identity_region)
        try:
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName='dataall', Namespace='default'
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
    def get_quicksight_client(AwsAccountId, region='eu-west-1'):
        """Returns a boto3 quicksight client in the provided account/region
        Args:
            AwsAccountId(str) : aws account id
            region(str) : aws region
        Returns : boto3.client ("quicksight")
        """
        identity_region = Quicksight.get_identity_region(AwsAccountId)
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('quicksight', region_name=region)

    @staticmethod
    def create_quicksight_default_group(AwsAccountId):
        """Creates a Quicksight group called dataall
        Args:
            AwsAccountId(str):  aws account

        Returns:dict
            quicksight.describe_group response
        """
        client = Quicksight.get_quicksight_client_in_identity_region(AwsAccountId)
        group = Quicksight.describe_group(client, AwsAccountId)
        if not group:
            logger.info('Attempting to create Quicksight group `dataall...')
            response = client.create_group(
                GroupName='dataall',
                Description='Default data.all group',
                AwsAccountId=AwsAccountId,
                Namespace='default',
            )
            logger.info(f'Quicksight group `dataall created {response}')
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName='dataall', Namespace='default'
            )
            return response
        return group

    @staticmethod
    def describe_group(client, AwsAccountId):
        try:
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName='dataall', Namespace='default'
            )
            logger.info(
                f'Quicksight `dataall` group already exists in {AwsAccountId} '
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
    def register_user(AwsAccountId, UserName, UserRole='READER'):
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

        Quicksight.create_quicksight_default_group(AwsAccountId)
        response = client.list_user_groups(
            UserName=UserName, AwsAccountId=AwsAccountId, Namespace='default'
        )
        print(f'list_user_groups {UserName}')
        print(response)
        if 'dataall' not in [g['GroupName'] for g in response['GroupList']]:
            logger.warning(f'Adding {UserName} to Quicksight dataall on {AwsAccountId}')
            response = client.create_group_membership(
                MemberName=UserName,
                GroupName='dataall',
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
            user = Quicksight.register_user(
                AwsAccountId=AwsAccountId, UserName=UserName, UserRole=UserRole
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
    def get_anonymous_session(AwsAccountId, region, UserName, DashboardId=None):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        response = client.generate_embed_url_for_anonymous_user(
            AwsAccountId=AwsAccountId,
            SessionLifetimeInMinutes=120,
            Namespace='default',
            SessionTags=[
                {'Key': 'dataall', 'Value': UserName},
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
            user = Quicksight.register_user(AwsAccountId, UserName, UserRole)
        else:
            # if user.get("Role",None) not in ["AUTHOR","ADMIN"]:
            user = Quicksight.register_user(AwsAccountId, UserName, UserRole)

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
    def create_data_source_vpc(AwsAccountId, region, UserName, vpnConnectionId):
        client = Quicksight.get_quicksight_client(AwsAccountId, region)
        user = Quicksight.describe_user(AwsAccountId, UserName)
        if not user:
            return False
        try:
            response = client.describe_data_source(
                AwsAccountId=AwsAccountId, DataSourceId="dataall-metadata-db"
            )

        except:
            aurora_params = SecretsManager.get_secret_value(
                AwsAccountId=AwsAccountId, region=region, secretId="abcde"
            )
            response = client.create_data_source(
                AwsAccountId=AwsAccountId,
                DataSourceId="dataall-metadata-db",
                Name="sample-aurora-db",
                Type="AURORA_POSTGRESQL",
                DataSourceParameters = {
                    'AuroraPostgreSqlParameters':{
                            'Host': "dataall-dev-db.cluster-cxf75rkkjzhz.eu-west-1.rds.amazonaws.com",
                            'Port': 5432,
                            'Database': "devdb",
                        }
                },
                Credentials = {
                    "CredentialPair": {
                        "Username": "dtaadmin",
                        "Password": ",B3jDZGa-9nbMq,kI780CIiPfPlR4BWj"
                    }
                },
                Permissions= [
                    {
                        "Principal": user.get('Arn'),
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
                VpcConnectionProperties = {
                    'VpcConnectionArn': f"arn:aws:quicksight:{region}:{AwsAccountId}:vpcConnection/{vpnConnectionId}"
                }
            )

        return True

    @staticmethod
    def create_data_set_from_source(AwsAccountId, region, UserName, dataSourceId, datasetId):
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

        response = client.create_data_set(
            AwsAccountId=AwsAccountId,
            DataSetId=datasetId,
            Name=datasetId,
            PhysicalTableMap={
                'string': {
                    'RelationalTable': {
                        'DataSourceArn': data_source.get('DataSource').get('Arn'),
                        'Catalog': 'string',
                        'Schema': 'string',
                        'Name': 'string',
                        'InputColumns': [
                            {
                                'Name': 'string',
                                'Type': 'STRING'
                            },
                        ]
                    }
                }},
            ImportMode= 'DIRECT_QUERY',
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
