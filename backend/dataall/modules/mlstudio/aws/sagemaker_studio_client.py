import logging

from dataall.base.aws.sts import SessionHelper
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioUser
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_client(AwsAccountId, region):
    session = SessionHelper.remote_session(AwsAccountId, region)
    return session.client('sagemaker', region_name=region)


def get_sagemaker_studio_domain(AwsAccountId, region, domain_name):
    """
    Sagemaker studio domain is limited to 5 per account/region
    RETURN: an existing domain or None if no domain is in the AWS account
    """
    client = get_client(AwsAccountId=AwsAccountId, region=region)
    try:
        domain_id_paginator = client.get_paginator('list_domains')
        for page in domain_id_paginator.paginate():
            for domain in page.get('Domains', []):
                if domain.get('DomainName') == domain_name:
                    return domain
        return dict()
    except ClientError as e:
        print(e)
        return dict()


class SagemakerStudioClient:
    """A Sagemaker studio proxy client that is used to send requests to AWS"""

    def __init__(self, sm_user: SagemakerStudioUser):
        self._client = get_client(AwsAccountId=sm_user.AWSAccountId, region=sm_user.region)
        self._sagemakerStudioDomainID = sm_user.sagemakerStudioDomainID
        self._sagemakerStudioUserNameSlugify = sm_user.sagemakerStudioUserNameSlugify

    def get_sagemaker_studio_user_presigned_url(self):
        try:
            response_signed_url = self._client.create_presigned_domain_url(
                DomainId=self._sagemakerStudioDomainID,
                UserProfileName=self._sagemakerStudioUserNameSlugify,
            )
            return response_signed_url['AuthorizedUrl']
        except ClientError:
            return ''

    def get_sagemaker_studio_user_status(self):
        try:
            response = self._client.describe_user_profile(
                DomainId=self._sagemakerStudioDomainID,
                UserProfileName=self._sagemakerStudioUserNameSlugify,
            )
            return response['Status']
        except ClientError as e:
            logger.error(f'Could not retrieve Studio user {self._sagemakerStudioUserNameSlugify} status due to: {e} ')
            return 'NOT FOUND'

    def get_sagemaker_studio_user_applications(self):
        _running_apps = []
        try:
            paginator_app = self._client.get_paginator('list_apps')
            response_paginator = paginator_app.paginate(
                DomainIdEquals=self._sagemakerStudioDomainID,
                UserProfileNameEquals=self._sagemakerStudioUserNameSlugify,
            )
            for _response_app in response_paginator:
                for _app in _response_app['Apps']:
                    if _app.get('Status') not in ['Deleted']:
                        _running_apps.append(
                            dict(
                                DomainId=_app.get('DomainId'),
                                UserProfileName=_app.get('UserProfileName'),
                                AppType=_app.get('AppType'),
                                AppName=_app.get('AppName'),
                                Status=_app.get('Status'),
                            )
                        )
            return _running_apps
        except ClientError as e:
            raise e


def sagemaker_studio_client(sm_user: SagemakerStudioUser) -> SagemakerStudioClient:
    """Factory method to retrieve the client to send request to AWS"""
    return SagemakerStudioClient(sm_user)
