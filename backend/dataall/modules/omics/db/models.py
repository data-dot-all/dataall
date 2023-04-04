"""ORM models for omics projects"""

from sqlalchemy import Column, String, Integer, ForeignKey

from dataall.db import Base
from dataall.db import Resource, utils


class OmicsProject(Resource, Base):
    """Describes ORM model for omics projects"""

    __tablename__ = 'omics_project'
    environmentUri = Column(String, ForeignKey("environment.environmentUri"), nullable=False)
    projectUri = Column(String, primary_key=True, default=utils.uuid('omics_project'))
    AWSAccountId = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    SamlAdminGroupName = Column(String, nullable=True)

#TODO: Define metadata that is stored in RDS database
