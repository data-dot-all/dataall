import logging
import re

from .sts import SessionHelper

logger = logging.getLogger(__name__)


class QuicksightClient:
    DEFAULT_GROUP_NAME = 'dataall'
    QUICKSIGHT_IDENTITY_REGIONS = [
        {'name': 'US East (N. Virginia)', 'code': 'us-east-1'},
        {'name': 'US East (Ohio)', 'code': 'us-east-2'},
        {'name': 'US West (Oregon)', 'code': 'us-west-2'},
        {'name': 'Europe (Frankfurt)', 'code': 'eu-central-1'},
        {'name': 'Europe (Stockholm)', 'code': 'eu-north-1'},
        {'name': 'Europe (Ireland)', 'code': 'eu-west-1'},
        {'name': 'Europe (London)', 'code': 'eu-west-2'},
        {'name': 'Europe (Paris)', 'code': 'eu-west-3'},
        {'name': 'Asia Pacific (Singapore)', 'code': 'ap-southeast-1'},
        {'name': 'Asia Pacific (Sydney)', 'code': 'ap-southeast-2'},
        {'name': 'Asia Pacific (Tokyo)', 'code': 'ap-northeast-1'},
        {'name': 'Asia Pacific (Seoul)', 'code': 'ap-northeast-2'},
        {'name': 'South America (São Paulo)', 'code': 'sa-east-1'},
        {'name': 'Canada (Central)', 'code': 'ca-central-1'},
        {'name': 'Asia Pacific (Mumbai)', 'code': 'ap-south-1'},
    ]

    def __init__(self):
        pass

    @staticmethod
    def get_quicksight_client(AwsAccountId, region, session_region='eu-west-1'):
        """Returns a boto3 quicksight client in the provided account/region
        Args:
            AwsAccountId(str) : aws account id
            region(str) : aws region of the environment
            session_region(str) : region to create the session
        Returns : boto3.client ("quicksight")
        """
        session = SessionHelper.remote_session(accountid=AwsAccountId, region=region)
        return session.client('quicksight', region_name=session_region)

    @staticmethod
    def get_identity_region(AwsAccountId, region):
        """Quicksight manages identities in one region, and there is no API to retrieve it
        However, when using Quicksight user/group apis in the wrong region,
        the client will throw and exception showing the region Quicksight's using as its
        identity region.
        Args:
            AwsAccountId(str) : aws account id
            AwsAccountId(str) : aws region of environment
        Returns: str
            the region quicksight uses as identity region
        """
        identity_region_rex = re.compile('Please use the (?P<region>.*) endpoint.')
        scp = 'with an explicit deny in a service control policy'
        index = 0
        while index < len(QuicksightClient.QUICKSIGHT_IDENTITY_REGIONS):
            try:
                identity_region = QuicksightClient.QUICKSIGHT_IDENTITY_REGIONS[index].get('code')
                index += 1
                client = QuicksightClient.get_quicksight_client(
                    AwsAccountId=AwsAccountId, region=region, session_region=identity_region
                )
                response = client.describe_account_settings(AwsAccountId=AwsAccountId)
                logger.info(f'Returning identity region = {identity_region} for account {AwsAccountId}')
                return identity_region
            except client.exceptions.AccessDeniedException as e:
                if scp in str(e):
                    logger.info(
                        f'Quicksight SCP found in {identity_region} for account {AwsAccountId}. Trying next region...'
                    )
                else:
                    logger.info(
                        f'Quicksight identity region is not {identity_region}, selecting correct region endpoint...'
                    )
                    match = identity_region_rex.findall(str(e))
                    if match:
                        identity_region = match[0]
                        logger.info(f'Returning identity region = {identity_region} for account {AwsAccountId}')
                        return identity_region
                    else:
                        raise e
        raise Exception(
            f'Quicksight subscription is inactive or the identity region has SCPs preventing access from data.all to account {AwsAccountId}'
        )

    @staticmethod
    def get_quicksight_client_in_identity_region(AwsAccountId, region):
        """Returns a boto3 quicksight client in the Quicksight identity region for the provided account
        Args:
            AwsAccountId(str) : aws account id
            region(str) : aws region of the environment
        Returns : boto3.client ("quicksight")

        """
        identity_region = QuicksightClient.get_identity_region(AwsAccountId, region)
        session = SessionHelper.remote_session(accountid=AwsAccountId, region=region)
        return session.client('quicksight', region_name=identity_region)

    @staticmethod
    def check_quicksight_enterprise_subscription(AwsAccountId, region=None):
        """Use the DescribeAccountSubscription operation to receive a description of a Amazon QuickSight account's subscription. A successful API call returns an AccountInfo object that includes an account's name, subscription status, authentication type, edition, and notification email address.
        Args:
            AwsAccountId(str) : aws account id
            region(str): aws region
        Returns: bool
            True if Quicksight Enterprise Edition is enabled in the AWS Account
        """
        logger.info(f'Checking Quicksight subscription in AWS account = {AwsAccountId}')
        client = QuicksightClient.get_quicksight_client(AwsAccountId=AwsAccountId, region=region, session_region=region)
        try:
            response = client.describe_account_subscription(AwsAccountId=AwsAccountId)
            if not response['AccountInfo']:
                raise Exception(f'Quicksight Enterprise Subscription not found in Account: {AwsAccountId}')
            else:
                if response['AccountInfo']['Edition'] not in ['ENTERPRISE', 'ENTERPRISE_AND_Q']:
                    raise Exception(
                        f'Quicksight Subscription found in Account: {AwsAccountId} of incorrect type: {response["AccountInfo"]["Edition"]}'
                    )
                else:
                    if response['AccountInfo']['AccountSubscriptionStatus'] == 'ACCOUNT_CREATED':
                        return True
                    else:
                        raise Exception(
                            f'Quicksight Subscription found in Account: {AwsAccountId} not active. Status = {response["AccountInfo"]["AccountSubscriptionStatus"]}'
                        )

        except client.exceptions.ResourceNotFoundException:
            raise Exception('Quicksight Enterprise Subscription not found')

        except client.exceptions.AccessDeniedException:
            raise Exception('Access denied to Quicksight for selected role')

    @staticmethod
    def create_quicksight_group(AwsAccountId, region, GroupName=DEFAULT_GROUP_NAME):
        """Creates a Quicksight group called GroupName
        Args:
            AwsAccountId(str):  aws account
            region: aws region
            GroupName(str): name of the QS group

        Returns:dict
            quicksight.describe_group response
        """
        client = QuicksightClient.get_quicksight_client_in_identity_region(AwsAccountId, region)
        group = QuicksightClient.describe_group(client, AwsAccountId, region, GroupName)
        if not group:
            if GroupName == QuicksightClient.DEFAULT_GROUP_NAME:
                logger.info(f'Initializing data.all default group = {GroupName}')
                QuicksightClient.check_quicksight_enterprise_subscription(AwsAccountId, region)

            logger.info(f'Attempting to create Quicksight group `{GroupName}...')
            response = client.create_group(
                GroupName=GroupName,
                Description='data.all group',
                AwsAccountId=AwsAccountId,
                Namespace='default',
            )
            logger.info(f'Quicksight group {GroupName} created {response}')
            response = client.describe_group(AwsAccountId=AwsAccountId, GroupName=GroupName, Namespace='default')
            return response
        return group

    @staticmethod
    def describe_group(client, AwsAccountId, region, GroupName=DEFAULT_GROUP_NAME):
        try:
            response = client.describe_group(AwsAccountId=AwsAccountId, GroupName=GroupName, Namespace='default')
            logger.info(
                f'Quicksight {GroupName} group already exists in {AwsAccountId} '
                f'(using identity region {QuicksightClient.get_identity_region(AwsAccountId, region)}): '
                f'{response}'
            )
            return response
        except client.exceptions.ResourceNotFoundException:
            logger.info(
                f'Creating Quicksight group in {AwsAccountId} (using identity region {QuicksightClient.get_identity_region(AwsAccountId, region)})'
            )
