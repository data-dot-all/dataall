import logging

from dataall.aws.handlers.sts import SessionHelper


log = logging.getLogger(__name__)


class EC2:

    @staticmethod
    def get_client(account_id: str, region: str, role=None):
        session = SessionHelper.remote_session(accountid=account_id, role=role)
        return session.client('ec2', region_name=region)

    @staticmethod
    def check_default_vpc_exists(AwsAccountId: str, region: str, role=None):
        log.info("Check that default VPC exists..")
        client = EC2.get_client(account_id=AwsAccountId, region=region, role=role)
        response = client.describe_vpcs(
            Filters=[{'Name': 'isDefault', 'Values': ['true']}]
        )
        vpcs = response['Vpcs']
        log.info(f"Default VPCs response: {vpcs}")
        if vpcs:
            return True
        return False
