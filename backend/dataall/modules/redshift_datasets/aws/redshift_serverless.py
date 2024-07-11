import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper


log = logging.getLogger(__name__)


class RedshiftServerless:
    def __init__(self, account_id: str, region: str, role=None) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region, role=role)
        self.client = session.client(service_name='redshift-serverless', region_name=region)

    def get_workgroup_arn(self, workgroup_name):
        try:
            log.info(f'Getting arn of {workgroup_name=}')
            response = self.client.get_workgroup(workgroupName=workgroup_name)
            return response.get('workgroup').get('workgroupArn')
        except ClientError as e:
            log.error(e)
            raise e
