import logging

from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger(__name__)


class VPCManager:
    def __init__(self):
        pass

    @staticmethod
    def client(AwsAccountId, region, role=None):
        session = SessionHelper.remote_session(accountid=AwsAccountId, role=role)
        return session.client('ec2', region_name=region)

    @staticmethod
    def check_vpc_exists(AwsAccountId, region, vpc_id, role=None, subnet_ids=[]):
        try:
            ec2 = VPCManager.client(AwsAccountId=AwsAccountId, region=region, role=role)
            response = ec2.describe_vpcs(VpcIds=[vpc_id])
        except ClientError as e:
            log.exception(f'VPC Id {vpc_id} Not Found: {e}')
            raise Exception(f'VPCNotFound: {vpc_id}')

        try:
            if subnet_ids:
                response = ec2.describe_subnets(
                    Filters=[
                        {
                            'Name': 'vpc-id',
                            'Values': [vpc_id]
                        },
                    ],
                    SubnetIds=subnet_ids
                )
        except ClientError as e:
            log.exception(f'Subnet Id {subnet_ids} Not Found: {e}')
            raise Exception(f'VPCSubnetsNotFound: {subnet_ids}')

        if not subnet_ids or len(response['Subnets']) != len(subnet_ids):
            raise Exception(f'Not All Subnets: {subnet_ids} Are Within the Specified VPC Id {vpc_id}')
