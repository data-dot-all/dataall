from sqlalchemy import Column, String, ForeignKey
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes
from dataall.base.db import Resource, Base, utils


class RedshiftDataset(DatasetBase):
    __tablename__ = 'redshift_dataset'
    datasetUri = Column(String, ForeignKey('dataset.datasetUri'), primary_key=True)
    connectionUri = Column(String, ForeignKey('redshift_connection.connectionUri'), nullable=False)
    database = Column(String, nullable=False)
    schema = Column(String, nullable=False)
    includePattern = Column(String, nullable=True)
    excludePattern = Column(String, nullable=True)
    datashareArn = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': DatasetTypes.Redshift,
    }


# TODO, migration script: ALTER TYPE SCHEMA.datasettype ADD VALUE 'Redshift';


class RedshiftConnection(Base, Resource):
    __tablename__ = 'redshift_connection'
    connectionUri = Column(String, primary_key=True, default=utils.uuid('connection'))
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    SamlGroupName = Column(String, nullable=False)
    redshiftType = Column(String, nullable=False)
    clusterId = Column(String, nullable=True)
    nameSpaceId = Column(String, nullable=True)
    workgroup = Column(String, nullable=True)
    redshiftUser = Column(String, nullable=True)
    secretArn = Column(String, nullable=True)
