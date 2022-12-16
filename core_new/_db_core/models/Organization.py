from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression
from enum import Enum

from backend.db import Base, Resource, utils

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
