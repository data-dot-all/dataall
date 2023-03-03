from sqlalchemy import Column, String

from .. import Base
from .. import Resource, utils
from sqlalchemy.dialects import postgresql


class DatasetTableColumn(Resource, Base):
    __tablename__ = 'dataset_table_column'
    datasetUri = Column(String, nullable=False)
    tableUri = Column(String, nullable=False)
    columnUri = Column(String, primary_key=True, default=utils.uuid('col'))
    AWSAccountId = Column(String, nullable=False)
    region = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=False)
    GlueTableName = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    typeName = Column(String, nullable=False)
    columnType = Column(
        String, default='column'
    )  # can be either "column" or "partition"
    lfTagKey = Column(postgresql.ARRAY(String))
    lfTagValue = Column(postgresql.ARRAY(String))
