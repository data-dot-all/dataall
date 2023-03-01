from dataall.core.environment.models import EnvironmentResource


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
