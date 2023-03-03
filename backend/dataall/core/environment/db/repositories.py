from dataall.core.environment.models import EnvironmentResource, EnvironmentParameter
from sqlalchemy.sql import and_


class EnvironmentResourceRepository:
    """The code that contains operation to update environment resources"""

    def __init__(self, session):
        self._session = session

    def create(self, environment_uri, resource_uri, resource_type):
        """Creates an environment resource"""
        resource = EnvironmentResource(
            environment_uri=environment_uri,
            resource_uri=resource_uri,
            resource_type=resource_type
        )

        self._session.add(resource)

    def delete(self, environment_uri, resource_uri, resource_type):
        """Deletes an environment resource"""
        resource = EnvironmentResource(
            environment_uri=environment_uri,
            resource_uri=resource_uri,
            resource_type=resource_type
        )

        self._session.query(EnvironmentResource).filter(EnvironmentResource == resource).delete()


class EnvironmentParameterRepository:
    """CRUD operations for EnvironmentParameter"""

    def __init__(self, session):
        self._session = session

    def get_param(self, env_uri, param_key):
        return self._session.query(EnvironmentParameter).filter(
            and_(
                EnvironmentParameter.environmentUri == env_uri,
                EnvironmentParameter.key == param_key
            )
        ).first()

    def get_params(self, env_uri):
        return self._session.query(EnvironmentParameter).filter(
            EnvironmentParameter.environmentUri == env_uri
        )

    def update_params(self, env_uri, params):
        """Rewrite all parameters for the environment"""
        self.delete_params(env_uri)
        self._session.add_all(params)

    def delete_params(self, env_uri):
        """Erase all environment parameters"""
        self._session.query(EnvironmentParameter).filter(
            EnvironmentParameter.environmentUri == env_uri
        ).delete()
