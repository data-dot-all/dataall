from dataall.core.environment.db.environment_models import EnvironmentParameter, Environment, EnvironmentGroup
from sqlalchemy.sql import and_

from dataall.base.db import exceptions


class EnvironmentParameterRepository:
    """CRUD operations for EnvironmentParameter"""

    def __init__(self, session):
        self._session = session

    def get_param(self, env_uri, param_key):
        return (
            self._session.query(EnvironmentParameter)
            .filter(and_(EnvironmentParameter.environmentUri == env_uri, EnvironmentParameter.key == param_key))
            .first()
        )

    def get_params(self, env_uri):
        return self._session.query(EnvironmentParameter).filter(EnvironmentParameter.environmentUri == env_uri)

    def update_params(self, env_uri, params):
        """Rewrite all parameters for the environment"""
        self.delete_params(env_uri)
        self._session.add_all(params)

    def delete_params(self, env_uri):
        """Erase all environment parameters"""
        self._session.query(EnvironmentParameter).filter(EnvironmentParameter.environmentUri == env_uri).delete()


class EnvironmentRepository:
    @staticmethod
    def get_environment_by_uri(session, uri):
        if not uri:
            raise exceptions.RequiredParameter('environmentUri')
        environment: Environment = session.query(Environment).get(uri)
        if not environment:
            raise exceptions.ObjectNotFound(Environment.__name__, uri)
        return environment

    @staticmethod
    def count_environments_with_organization_uri(session, uri):
        return session.query(Environment).filter(Environment.organizationUri == uri).count()

    @staticmethod
    def count_environments_with_organization_and_group(session, organization, group):
        return (
            session.query(Environment)
            .filter(
                and_(
                    Environment.organizationUri == organization.organizationUri,
                    Environment.SamlGroupName == group,
                )
            )
            .count()
        )

    @staticmethod
    def find_environment_by_account_region(session, account_id, region):
        environment: Environment = (
            session.query(Environment)
            .filter(and_(Environment.AwsAccountId == account_id, Environment.region == region))
            .first()
        )
        if not environment:
            return None
        return environment


class EnvironmentGroupRepository:
    @staticmethod
    def get_group_by_uri_from_group_list(session, environmentUri, groups) -> EnvironmentGroup:
        return (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == environmentUri,
                    EnvironmentGroup.groupUri.in_(groups),
                )
            )
            .first()
        )

    @staticmethod
    def get_group_by_uri(session, environmentUri, groupUri) -> EnvironmentGroup:
        return (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == environmentUri,
                    EnvironmentGroup.groupUri == groupUri,
                )
            )
            .first()
        )
