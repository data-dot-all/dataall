"""The package contains the database models that are related to the environment"""

from sqlalchemy import Column, String, ForeignKey
from dataall.db import Resource, Base


class EnvironmentParameter(Resource, Base):
    """Represent the parameter of the environment"""
    __tablename__ = 'environment_parameters'
    environmentUri = Column(String, ForeignKey("environment.environmentUri"), primary_key=True)
    paramKey = Column('paramKey', String, primary_key=True),
    paramValue = Column('paramValue', String, nullable=True)


class EnvironmentResource(Resource, Base):
    """Represents a resource that is allocated in the AWS and belongs to the environment"""
    __tablename__ = "environment_resources"
    environmentUri = Column(String, primary_key=True)
    resourceUri = Column(String, primary_key=True),
    resourceType = Column(String, nullable=False)
