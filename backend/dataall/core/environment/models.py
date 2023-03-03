"""The package contains the database models that are related to the environment"""

from sqlalchemy import Column, String, ForeignKey
from dataall.db import Resource, Base


class EnvironmentParameter(Base):
    """Represent the parameter of the environment"""
    __tablename__ = 'environment_parameters'
    environmentUri = Column(String, ForeignKey("environment.environmentUri"), primary_key=True)
    key = Column('paramKey', String, primary_key=True)
    value = Column('paramValue', String, nullable=True)

    def __init__(self, env_uri, key, value):
        self.environmentUri = env_uri
        self.key = key
        self.value = value

    def __repr__(self):
        return f'EnvironmentParameter(paramKey={self.key}, paramValue={self.value})'


class EnvironmentResource(Base):
    """Represents a resource that is allocated in the AWS and belongs to the environment"""
    __tablename__ = "environment_resources"
    environmentUri = Column(String, primary_key=True)
    resourceUri = Column(String, primary_key=True)
    resourceType = Column(String, nullable=False)

    def __init__(self, environment_uri, resource_uri, resource_type):
        self.environmentUri = environment_uri
        self.resourceType = resource_type
        self.resourceUri = resource_uri
