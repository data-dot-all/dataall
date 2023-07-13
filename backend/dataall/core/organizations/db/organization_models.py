import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import query_expression

from dataall.db import Base
from dataall.db import Resource, utils


class OrganisationUserRole(Enum):
    Owner = '999'
    Admin = '900'
    Member = '100'
    NotMember = '000'
    Invited = '800'


class Organization(Resource, Base):
    __tablename__ = 'organization'
    organizationUri = Column(
        String, primary_key=True, default=utils.uuid('organization')
    )

    # `role` is a dynamically generated SQL expression
    # computing the role of the user in an organization
    userRoleInOrganization = query_expression()
    SamlGroupName = Column(String, nullable=True)


class OrganizationGroup(Base):
    __tablename__ = 'organization_group'
    groupUri = Column(String, primary_key=True)
    organizationUri = Column(String, primary_key=True)
    invitedBy = Column(String, nullable=True)
    description = Column(String, default='No description provided')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
