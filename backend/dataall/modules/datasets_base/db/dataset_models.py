from sqlalchemy import Boolean, Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.orm import query_expression
from dataall.base.db import Base, Resource, utils
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language, DatasetType


class DatasetBase(Resource, Base):
    __tablename__ = 'dataset'
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    organizationUri = Column(String, nullable=False)
    datasetUri = Column(String, primary_key=True, default=utils.uuid('dataset'))
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    userRoleForDataset = query_expression()
    userRoleInEnvironment = query_expression()
    isPublishedInEnvironment = query_expression()
    projectPermission = query_expression()
    language = Column(String, nullable=False, default=Language.English.value)
    topics = Column(ARRAY(String), nullable=True)
    confidentiality = Column(String, nullable=False, default=ConfidentialityClassification.Unclassified.value)
    tags = Column(ARRAY(String))
    inProject = query_expression()

    businessOwnerEmail = Column(String, nullable=True)
    businessOwnerDelegationEmails = Column(ARRAY(String), nullable=True)
    stewards = Column(String, nullable=True)

    SamlAdminGroupName = Column(String, nullable=True)
    autoApprovalEnabled = Column(Boolean, default=False)

    datasetType = Column(Enum(DatasetType), nullable=False, default=DatasetType.S3)
    imported = Column(Boolean, default=False)

    __mapper_args__ = {'polymorphic_identity': 'dataset', 'polymorphic_on': datasetType}

    @classmethod
    def uri(cls):
        return cls.datasetUri


DatasetBase.__name__ = 'Dataset'


class DatasetLock(Base):
    __tablename__ = 'dataset_lock'
    datasetUri = Column(String, ForeignKey('dataset.datasetUri'), nullable=False, primary_key=True)
    isLocked = Column(Boolean, default=False)
    acquiredBy = Column(String, nullable=True)

    def __init__(self, datasetUri, isLocked=False, acquiredBy=None):
        self.datasetUri = datasetUri
        self.isLocked = isLocked
        self.acquiredBy = acquiredBy
