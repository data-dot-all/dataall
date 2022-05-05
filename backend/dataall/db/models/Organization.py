from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression

from .. import Base
from .. import Resource, utils


class Organization(Resource, Base):
    __tablename__ = "organization"
    organizationUri = Column(String, primary_key=True, default=utils.uuid("organization"))

    # `role` is a dynamically generated SQL expression
    # computing the role of the user in an organization
    userRoleInOrganization = query_expression()
    SamlGroupName = Column(String, nullable=True)
