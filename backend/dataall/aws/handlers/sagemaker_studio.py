from botocore.exceptions import ClientError

from .parameter_store import ParameterStoreManager
from .sts import SessionHelper
from ...db.models import Environment


# TODO: cannot be deleted because it is used in environment cdk stack --> there are changes in V1.5 affect this implementation. We need to rebase before continuing
class SagemakerStudio:
    @staticmethod
    def client(AwsAccountId, region, role=None):
        session = SessionHelper.remote_session(accountid=AwsAccountId, role=role)
        return session.client('sagemaker', region_name=region)

    @staticmethod
    def get_sagemaker_studio_domain(AwsAccountId, region, role=None):
        """
        Sagemaker studio domain is limited to one per account,
        RETURN: an existing domain or None if no domain is in the AWS account
        """

        client = SagemakerStudio.client(AwsAccountId=AwsAccountId, region=region, role=role)
        existing_domain = dict()
        try:
            domain_id_paginator = client.get_paginator('list_domains')
            domains = domain_id_paginator.paginate()
            for _domain in domains:
                print(_domain)
                for _domain in _domain.get('Domains'):
                    # Get the domain name created by dataall
                    if 'dataall' in _domain:
                        return _domain
                    else:
                        existing_domain = _domain
            return existing_domain
        except ClientError as e:
            print(e)
            return 'NotFound'
