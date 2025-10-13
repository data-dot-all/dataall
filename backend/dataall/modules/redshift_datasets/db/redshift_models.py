from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes
from dataall.base.db import Resource, Base, utils


class RedshiftConnection(Base, Resource):
    __tablename__ = 'redshift_connection'
    connectionUri = Column(String, primary_key=True, default=utils.uuid('connection'))
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    SamlGroupName = Column(String, nullable=False)
    redshiftType = Column(String, nullable=False)
    clusterId = Column(String, nullable=True)
    nameSpaceId = Column(String, nullable=True)
    workgroup = Column(String, nullable=True)
    database = Column(String, nullable=False)
    redshiftUser = Column(String, nullable=True)
    secretArn = Column(String, nullable=True)
    encryptionType = Column(String, nullable=True)
    connectionType = Column(String, nullable=False)


class RedshiftDataset(DatasetBase):
    __tablename__ = 'redshift_dataset'
    datasetUri = Column(String, ForeignKey('dataset.datasetUri'), primary_key=True)
    connectionUri = Column(String, ForeignKey('redshift_connection.connectionUri'), nullable=False)
    schema = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': DatasetTypes.Redshift,
    }


class RedshiftTable(Base, Resource):
    __tablename__ = 'redshift_table'
    datasetUri = Column(String, ForeignKey('redshift_dataset.datasetUri', ondelete='CASCADE'), nullable=False)
    rsTableUri = Column(String, primary_key=True, default=utils.uuid('rs_table'))
    topics = Column(ARRAY(String), nullable=True)

    @classmethod
    def uri_column(cls):
        return cls.rsTableUri
