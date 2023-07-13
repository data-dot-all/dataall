"""The package contains the database models that are related to the environment"""
import datetime

from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from sqlalchemy.orm import query_expression
from dataall.db import Resource, Base, utils

from dataall.core.environment.api.enums import EnvironmentPermission


class Environment(Resource, Base):
    __tablename__ = 'environment'
    organizationUri = Column(String, nullable=False)
    environmentUri = Column(String, primary_key=True, default=utils.uuid('environment'))
    AwsAccountId = Column(String, nullable=False)
    region = Column(String, nullable=False, default='eu-west-1')
    cognitoGroupName = Column(String, nullable=True)
    resourcePrefix = Column(String, nullable=False, default='dataall')

    validated = Column(Boolean, default=False)
    environmentType = Column(String, nullable=False, default='Data')
    isOrganizationDefaultEnvironment = Column(Boolean, default=False)
    EnvironmentDefaultIAMRoleName = Column(String, nullable=False)
    EnvironmentDefaultIAMRoleImported = Column(Boolean, default=False)
    EnvironmentDefaultIAMRoleArn = Column(String, nullable=False)
    EnvironmentDefaultBucketName = Column(String)
    EnvironmentDefaultAthenaWorkGroup = Column(String)
    roleCreated = Column(Boolean, nullable=False, default=False)

    userRoleInEnvironment = query_expression()

    SamlGroupName = Column(String, nullable=True)
    CDKRoleArn = Column(String, nullable=False)

    subscriptionsEnabled = Column(Boolean, default=False)
    subscriptionsProducersTopicName = Column(String)
    subscriptionsProducersTopicImported = Column(Boolean, default=False)
    subscriptionsConsumersTopicName = Column(String)
    subscriptionsConsumersTopicImported = Column(Boolean, default=False)


class EnvironmentGroup(Base):
    __tablename__ = 'environment_group_permission'
    groupUri = Column(String, primary_key=True)
    environmentUri = Column(String, primary_key=True)
    invitedBy = Column(String, nullable=True)
    environmentIAMRoleArn = Column(String, nullable=True)
    environmentIAMRoleName = Column(String, nullable=True)
    environmentIAMRoleImported = Column(Boolean, default=False)
    environmentAthenaWorkGroup = Column(String, nullable=True)
    description = Column(String, default='No description provided')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)

    # environmentRole is the role of the entity (group or user) in the Environment
    groupRoleInEnvironment = Column(
        String, nullable=False, default=EnvironmentPermission.Invited.value
    )


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
