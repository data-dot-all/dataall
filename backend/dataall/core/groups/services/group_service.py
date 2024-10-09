import os

from dataall.base.services.service_provider_factory import ServiceProviderFactory
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.base.context import get_context


class GroupService:
    LOCAL_TEST_GROUPS = [
        'Engineers',
        'Scientists',
        'Requesters',
        'Producers',
        'Consumers',
    ]

    @staticmethod
    def _list_cognito_groups():
        # for test environment
        envname = os.getenv('envname', 'local')
        if envname in ['dkrcompose']:
            return GroupService.LOCAL_TEST_GROUPS

        # for real environment
        current_region = os.getenv('AWS_REGION', 'eu-west-1')
        service_provider = ServiceProviderFactory.get_service_provider_instance()
        groups = service_provider.list_groups(envname=envname, region=current_region)
        return groups

    @staticmethod
    def _list_invited_groups(session, filter: dict = None):
        category, category_uri = filter.get('type'), filter.get('uri')
        if not (category and category_uri):
            return []

        invited_groups = []
        if category == 'environment':
            invited_groups = EnvironmentService.get_all_environment_groups(
                session=session,
                uri=category_uri,
                filter=None,
            ).all()
        if category == 'organization':
            organization = OrganizationRepository.get_organization_by_uri(session, category_uri)
            invited_groups = OrganizationRepository.query_organization_groups(
                session=session,
                uri=organization.organizationUri,
                filter=None,
            ).all()

        return [item.groupUri for item in invited_groups]

    @staticmethod
    def get_groups_for_user(userId):
        # for test environment
        envname = os.getenv('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            return GroupService.LOCAL_TEST_GROUPS

        # for real environment
        service_provider = ServiceProviderFactory.get_service_provider_instance()
        groups = service_provider.get_groups_for_user(userId)
        return groups

    @staticmethod
    def get_user_list_for_group(groupUri):
        try:
            service_provider = ServiceProviderFactory.get_service_provider_instance()
            user_list = service_provider.get_user_list_from_group(groupUri)
            return user_list
        except Exception as e:
            raise Exception(f'Failed to get users list for group {groupUri}. Error: {e}')

    @staticmethod
    def list_groups_without_invited(filter: dict = None):
        with get_context().db_engine.scoped_session() as session:
            cognito_groups = GroupService._list_cognito_groups()
            invited_groups = GroupService._list_invited_groups(session, filter)

            groups = []
            for group in cognito_groups:
                if group not in invited_groups:
                    groups.append({'groupName': group})

            return groups
