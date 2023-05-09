import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.notebooks.db.models import SagemakerNotebook
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SagemakerStudioClient:
    """
    A Sagemaker studio proxy client that is used to send requests to AWS
    """

    def __init__(self, environment:Environment):
        session = SessionHelper.remote_session(environment.AWSAccountId)
        self._client = session.client('sagemaker', region_name=environment.region)
        self._domain_name = ''

    def get_sagemaker_studio_domain(self):
        """
        Sagemaker studio domain is limited to one per account,
        RETURN: an existing domain or None if no domain is in the AWS account
        """
        existing_domain = dict()
        try:
            domain_id_paginator = self._client.get_paginator('list_domains')
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

    def presigned_url(self,
        sagemakerStudioDomainID,
        sagemakerStudioUserProfileNameSlugify,
    ):
        try:
            response_signed_url =  self._client.create_presigned_domain_url(
                DomainId=sagemakerStudioDomainID,
                UserProfileName=sagemakerStudioUserProfileNameSlugify,
            )
            return response_signed_url['AuthorizedUrl']
        except ClientError:
            return ''

    def get_user_profile_status(self,
        sagemakerStudioDomainID,
        sagemakerStudioUserProfileNameSlugify,
    ):
        try:
            response =  self._client.describe_user_profile(
                DomainId=sagemakerStudioDomainID,
                UserProfileName=sagemakerStudioUserProfileNameSlugify,
            )
            return response['Status']
        except ClientError as e:
            print(e)
            return 'NotFound'

    def get_user_profile_applications(self,
        sagemakerStudioDomainID,
        sagemakerStudioUserProfileNameSlugify,
    ):
        _running_apps = []
        try:
            paginator_app =  self._client.get_paginator('list_apps')
            response_paginator = paginator_app.paginate(
                DomainIdEquals=sagemakerStudioDomainID,
                UserProfileNameEquals=sagemakerStudioUserProfileNameSlugify,
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

def sm_studio_client(environment: Environment) -> SagemakerStudioClient:
    """Factory method to retrieve the client to send request to AWS"""
    return SagemakerStudioClient(environment)
