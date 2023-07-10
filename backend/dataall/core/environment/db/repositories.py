from dataall.core.environment.db.models import EnvironmentParameter
from sqlalchemy.sql import and_


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
