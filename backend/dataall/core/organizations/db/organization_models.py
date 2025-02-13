import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import query_expression

from dataall.base.db import Base
from dataall.base.db import Resource, utils

from dataall.core.metadata_manager import MetadataFormEntityManager, MetadataFormEntity, MetadataFormEntityTypes


class Organization(Resource, Base):
    __metaclass__ = MetadataFormEntity
    __tablename__ = 'organization'
    organizationUri = Column(String, primary_key=True, default=utils.uuid('organization'))

    # `role` is a dynamically generated SQL expression
    # computing the role of the user in an organization
    userRoleInOrganization = query_expression()
    SamlGroupName = Column(String, nullable=True)

    def uri(self):
        return self.organizationUri

    def owner_name(self):
        return self.SamlGroupName

    def entity_name(self):
        return self.label


class OrganizationGroup(Base):
    __metaclass__ = MetadataFormEntity
    __tablename__ = 'organization_group'
    groupUri = Column(String, primary_key=True)
    organizationUri = Column(String, primary_key=True)
    invitedBy = Column(String, nullable=True)
    description = Column(String, default='No description provided')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)

    def uri(self):
        return f'{self.groupUri}-{self.organizationUri}'

    def owner_name(self):
        return self.invitedBy

    def entity_name(self):
        return f'{self.groupUri}-{self.organizationUri}'


MetadataFormEntityManager.register(Organization, MetadataFormEntityTypes.Organization.value)
MetadataFormEntityManager.register(OrganizationGroup, MetadataFormEntityTypes.OrganizationTeam.value)
