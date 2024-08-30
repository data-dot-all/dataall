from dataall.base.context import get_context
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.metadata_forms.db.enums import MetadataFormUserRoles, MetadataFormEntityTypes
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository
from functools import wraps
from dataall.base.db import exceptions


class MetadataFormAccessService:
    @staticmethod
    def is_owner(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return MetadataFormRepository.get_metadata_form_owner(session, uri) in context.groups

    @staticmethod
    def can_perform(action: str):
        def decorator(f):
            @wraps(f)
            def check_permission(*args, **kwds):
                uri = kwds.get('uri')
                if not uri:
                    raise KeyError(f"{f.__name__} doesn't have parameter uri.")

                if MetadataFormAccessService.is_owner(uri):
                    return f(*args, **kwds)
                else:
                    raise exceptions.UnauthorizedOperation(
                        action=action,
                        message=f'User {get_context().username} is not the owner of the metadata form {uri}',
                    )

            return check_permission

        return decorator

    @staticmethod
    def get_user_role(uri):
        if MetadataFormAccessService.is_owner(uri):
            return MetadataFormUserRoles.Owner.value
        else:
            return MetadataFormUserRoles.User.value

    @staticmethod
    def _target_org_uri_getter(entityType, entityUri):
        if not entityType or not entityUri:
            return None
        if entityType == MetadataFormEntityTypes.Organizations.value:
            return entityUri
        elif entityType == MetadataFormEntityTypes.Environments.value:
            with get_context().db_engine.scoped_session() as session:
                return EnvironmentRepository.get_environment_by_uri(session, entityUri).organizationUri
        elif entityType == MetadataFormEntityTypes.Datasets.value:
            with get_context().db_engine.scoped_session() as session:
                return DatasetBaseRepository.get_dataset_by_uri(session, entityUri).organizationUri
        else:
            # toDo add other entities
            return None

    @staticmethod
    def _target_env_uri_getter(entityType, entityUri):
        if not entityType or not entityUri:
            return None
        if entityType == MetadataFormEntityTypes.Organizations.value:
            return None
        elif entityType == MetadataFormEntityTypes.Environments.value:
            return entityUri
        elif entityType == MetadataFormEntityTypes.Datasets.value:
            with get_context().db_engine.scoped_session() as session:
                return DatasetBaseRepository.get_dataset_by_uri(session, entityUri).environmentUri
        else:
            # toDo add other entities
            return None

    @staticmethod
    def get_target_orgs_and_envs(username, groups, is_da_admin=False, filter={}):
        envs = None
        orgs = None
        target_org_uri = MetadataFormAccessService._target_org_uri_getter(
            filter.get('entityType'), filter.get('entityUri')
        )
        target_env_uri = MetadataFormAccessService._target_env_uri_getter(
            filter.get('entityType'), filter.get('entityUri')
        )
        # is user is no dataall admin, query_metadata_forms requires arrays of users envs and orgs uris
        if not is_da_admin:
            with get_context().db_engine.scoped_session() as session:
                envs = EnvironmentRepository.query_user_environments(session, username, groups, {})
                envs = [e.environmentUri for e in envs]
                orgs = OrganizationRepository.query_user_organizations(session, username, groups, {})
                orgs = [o.organizationUri for o in orgs]
        if target_org_uri:
            if orgs and target_org_uri not in orgs:
                raise exceptions.UnauthorizedOperation(
                    action='GET METADATA FORM LIST',
                    message=f'User {username} can not view organization {target_org_uri}',
                )
            orgs = [target_org_uri]

        if target_env_uri:
            if envs and target_env_uri not in envs:
                raise exceptions.UnauthorizedOperation(
                    action='GET METADATA FORM LIST',
                    message=f'User {username} can not view environment {target_env_uri}',
                )
            envs = [target_env_uri]

        if filter.get('entityType') == MetadataFormEntityTypes.Organizations.value:
            envs = []

        return orgs, envs
