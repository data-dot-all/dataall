from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import query_expression

from .. import Base, Resource, utils


class DatasetStorageLocation(Resource, Base):
    __tablename__ = 'dataset_storage_location'
    datasetUri = Column(String, nullable=False)
    locationUri = Column(String, primary_key=True, default=utils.uuid('location'))
    AWSAccountId = Column(String, nullable=False)
    S3BucketName = Column(String, nullable=False)
    S3Prefix = Column(String, nullable=False)
    S3AccessPoint = Column(String, nullable=True)
    region = Column(String, default='eu-west-1')
    locationCreated = Column(Boolean, default=False)
    userRoleForStorageLocation = query_expression()
    projectPermission = query_expression()
    environmentEndPoint = query_expression()
