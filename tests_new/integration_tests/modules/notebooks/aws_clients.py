import logging
import json
from typing import Any, Dict, Optional
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class VpcClient:
    def __init__(self, session, region):
        self._client = session.client('ec2', region_name=region)
        self._region = region

    def create_vpc(self, vpc_name: str, cidr: str = '10.0.0.0/28') -> str:
        log.info('Creating VPC..')
        response = self._client.create_vpc(
            CidrBlock=cidr,
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {'Key': 'Name', 'Value': vpc_name},
                    ],
                },
            ],
        )
        vpc_id = response['Vpc']['VpcId']
        log.info(f'VPC created with ID: {vpc_id=}')
        return vpc_id

    def delete_vpc(self, vpc_id: str) -> Dict[str, Any]:
        log.info('Deleting VPC..')
        response = self._client.delete_vpc(VpcId=vpc_id)
        log.info(f'VPC deleted with ID: {vpc_id=}')
        return response

    def get_vpc_id_by_name(self, vpc_name: str) -> Optional[str]:
        log.info('Getting VPC ID by name..')
        response = self._client.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [vpc_name]}])
        if len(response['Vpcs']) == 0:
            log.info(f'VPC with name {vpc_name} not found')
            return None
        vpc_id = response['Vpcs'][0]['VpcId']
        log.info(f'VPC ID found: {vpc_id=}')
        return vpc_id

    def delete_vpc_by_name(self, vpc_name: str):
        try:
            vpc_id = self.get_vpc_id_by_name(vpc_name)
            if vpc_id:
                self.delete_vpc(vpc_id)
            return True
        except Exception as e:
            log.error(f'Error deleting vpc {vpc_name=}. Error Message: {e}')

    def create_subnet(self, vpc_id: str, subnet_name: str, cidr: str) -> str:
        log.info('Creating subnet..')
        response = self._client.create_subnet(
            VpcId=vpc_id,
            CidrBlock=cidr,
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {'Key': 'Name', 'Value': subnet_name},
                    ],
                },
            ],
        )
        subnet_id = response['Subnet']['SubnetId']
        log.info(f'Subnet created with ID: {subnet_id=}')
        return subnet_id

    def get_subnet_id_by_name(self, subnet_name: str) -> Optional[str]:
        log.info('Getting subnet ID by name..')
        response = self._client.describe_subnets(Filters=[{'Name': 'tag:Name', 'Values': [subnet_name]}])
        if len(response['Subnets']) == 0:
            log.info(f'Subnet with name {subnet_name} not found')
            return None
        subnet_id = response['Subnets'][0]['SubnetId']
        log.info(f'Subnet ID found: {subnet_id=}')
        return subnet_id

    def delete_subnet(self, subnet_id: str) -> Dict[str, Any]:
        log.info('Deleting subnet..')
        response = self._client.delete_subnet(SubnetId=subnet_id)
        log.info(f'Subnet deleted with ID: {subnet_id=}')
        return response

    def delete_subnet_by_name(self, subnet_name: str):
        try:
            subnet_id = self.get_subnet_id_by_name(subnet_name)
            if subnet_id:
                self.delete_subnet(subnet_id)
            return True
        except Exception as e:
            log.error(f'Error deleting subnet {subnet_name=}. Error Message: {e}')
