import enum

from sqlalchemy import Column, String, ForeignKey

from dataall.base.db import Base
from dataall.base.db import Resource, utils


class OmicsWorkflow(Resource, Base):
    __tablename__ = 'omics_workflow'
    workflowUri = Column(String, primary_key=True, default=utils.uuid('omicsWorkflowUri'))
    arn = Column(String, nullable=False)
    id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    environmentUri = Column(String, nullable=True)


class OmicsRun(Resource, Base):
    __tablename__ = 'omics_run'
    runUri = Column(String, nullable=False, primary_key=True, default=utils.uuid('runUri'))
    organizationUri = Column(String, nullable=False)
    environmentUri = Column(String, ForeignKey('environment.environmentUri', ondelete='cascade'), nullable=False)
    workflowUri = Column(String, ForeignKey('omics_workflow.workflowUri', ondelete='cascade'), nullable=False)
    SamlAdminGroupName = Column(String, nullable=False)
    parameterTemplate = Column(String, nullable=False)
    outputUri = Column(String, nullable=True)
    outputDatasetUri = Column(String, nullable=True)
