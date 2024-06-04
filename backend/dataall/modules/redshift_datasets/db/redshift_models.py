from sqlalchemy import Column, String, ForeignKey
from dataall.modules.connections_base.db.connection_models import Connection
from dataall.modules.connections_base.api.enums import ConnectionType
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.services.datasets_enums import DatasetType


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
        'polymorphic_identity': DatasetType.Redshift,
    }


# TODO, migration script: ALTER TYPE SCHEMA.datasettype ADD VALUE 'Redshift';


class RedshiftConnection(Connection):
    __tablename__ = 'redshift_connection'
    connectionUri = Column(String, ForeignKey('connection.connectionUri'), primary_key=True)
    redshiftType = Column(String, nullable=False)
    clusterId = Column(String, nullable=True)
    nameSpaceId = Column(String, nullable=True)
    workgroupId = Column(String, nullable=True)
    redshiftUser = Column(String, nullable=True)
    secretArn = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': ConnectionType.Redshift,
    }
