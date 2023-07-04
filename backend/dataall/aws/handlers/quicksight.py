import logging
import re

from .sts import SessionHelper

logger = logging.getLogger('QuicksightHandler')
logger.setLevel(logging.DEBUG)


class QuicksightClient:

    DEFAULT_GROUP_NAME = 'dataall'

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
        session = SessionHelper.remote_session(accountid=AwsAccountId)
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
        client = QuicksightClient.get_quicksight_client(AwsAccountId=AwsAccountId, region=identity_region)
        try:
            response = client.describe_group(
                AwsAccountId=AwsAccountId, GroupName=QuicksightClient.DEFAULT_GROUP_NAME, Namespace='default'
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
        identity_region = QuicksightClient.get_identity_region(AwsAccountId)
        session = SessionHelper.remote_session(accountid=AwsAccountId)
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
        client = QuicksightClient.get_quicksight_client(AwsAccountId=AwsAccountId, region=region)
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
            raise Exception('Access denied to Quicksight for selected role')
        return False

    @staticmethod
    def create_quicksight_group(AwsAccountId, GroupName=DEFAULT_GROUP_NAME):
        """Creates a Quicksight group called GroupName
        Args:
            AwsAccountId(str):  aws account
            GroupName(str): name of the QS group

        Returns:dict
            quicksight.describe_group response
        """
        client = QuicksightClient.get_quicksight_client_in_identity_region(AwsAccountId)
        group = QuicksightClient.describe_group(client, AwsAccountId, GroupName)
        if not group:
            if GroupName == QuicksightClient.DEFAULT_GROUP_NAME:
                logger.info(f'Initializing data.all default group = {GroupName}')
                QuicksightClient.check_quicksight_enterprise_subscription(AwsAccountId)

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
                f'(using identity region {QuicksightClient.get_identity_region(AwsAccountId)}): '
                f'{response}'
            )
            return response
        except client.exceptions.ResourceNotFoundException:
            logger.info(
                f'Creating Quicksight group in {AwsAccountId} (using identity region {QuicksightClient.get_identity_region(AwsAccountId)})'
            )
