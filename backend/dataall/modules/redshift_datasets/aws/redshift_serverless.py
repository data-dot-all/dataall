import logging
from typing import List
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper


log = logging.getLogger(__name__)


class RedshiftServerlessClient:
    def __init__(self, account_id: str, region: str, role=None) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region, role=role)
        self.client = session.client(service_name='redshift-serverless', region_name=region)

    def get_namespace_by_id(self, namespace_id: str):
        log.info(f'Get namespace with {namespace_id=}')
        response = self.client.list_namespaces()
        namespaces = response.get('namespaces', [])
        namespaces_filtered = [namespace for namespace in namespaces if namespace['namespaceId'] == namespace_id]
        return namespaces_filtered[0] if namespaces_filtered else None

    def list_workgroups_in_namespace(self, namespace_name: str) -> List[dict]:
        log.info(f'Listing workgroups in {namespace_name=}')
        response = self.client.list_workgroups()
        workgroups = response.get('workgroups', [])
        return [wg for wg in workgroups if wg['namespaceName'] == namespace_name]

    def get_workgroup_arn(self, workgroup_name: str) -> str:
        try:
            log.info(f'Getting arn of {workgroup_name=}')
            response = self.client.get_workgroup(workgroupName=workgroup_name)
            return response.get('workgroup').get('workgroupArn')
        except ClientError as e:
            log.error(e)
            raise e


def redshift_serverless_client(account_id: str, region: str, role: str = None) -> RedshiftServerlessClient:
    "Factory of Client"
    return RedshiftServerlessClient(account_id=account_id, region=region, role=role)
