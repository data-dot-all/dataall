from botocore.exceptions import ClientError

from .parameter_store import ParameterStoreManager
from .sts import SessionHelper
from ...db.models import Environment


class SagemakerStudio:
    @staticmethod
    def client(AwsAccountId, region):
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('sagemaker', region_name=region)

    @staticmethod
    def get_sagemaker_studio_domain(AwsAccountId, region):
        """
        Sagemaker studio domain is limited to one per account,
        RETURN: an existing domain or None if no domain is in the AWS account
        """
        client = SagemakerStudio.client(AwsAccountId, region)
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

    @staticmethod
    def presigned_url(
        AwsAccountId,
        region,
        sagemakerStudioDomainID,
        sagemakerStudioUserProfileNameSlugify,
    ):
        client = SagemakerStudio.client(AwsAccountId, region)
        try:
            response_signed_url = client.create_presigned_domain_url(
                DomainId=sagemakerStudioDomainID,
                UserProfileName=sagemakerStudioUserProfileNameSlugify,
            )
            return response_signed_url['AuthorizedUrl']
        except ClientError:
            return ''

    @staticmethod
    def get_user_profile_status(
        AwsAccountId,
        region,
        sagemakerStudioDomainID,
        sagemakerStudioUserProfileNameSlugify,
    ):
        client = SagemakerStudio.client(AwsAccountId, region)
        try:
            response = client.describe_user_profile(
                DomainId=sagemakerStudioDomainID,
                UserProfileName=sagemakerStudioUserProfileNameSlugify,
            )
            return response['Status']
        except ClientError as e:
            print(e)
            return 'NotFound'

    @staticmethod
    def get_user_profile_applications(
        AwsAccountId,
        region,
        sagemakerStudioDomainID,
        sagemakerStudioUserProfileNameSlugify,
    ):
        client = SagemakerStudio.client(AwsAccountId, region)
        _running_apps = []
        try:
            paginator_app = client.get_paginator('list_apps')
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
