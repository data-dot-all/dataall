from sqlalchemy import Column, String

from dataall.modules.dataset_sharing_base.db.share_object_base_models import ShareObjectItem
from dataall.modules.dataset_sharing_base.services.dataset_sharing_base_enums import ShareableType

#TODO: investigate migration for new tables

class TableShareObjectItem(ShareObjectItem):
    __tablename__ = 'table_share_object_item'
    GlueDatabaseName = Column(String, nullable=True)
    GlueTableName = Column(String, nullable=True)
    __mapper_args__ = {
        "polymorphic_identity": ShareableType.Table.value
    }

class FolderShareObjectItem(ShareObjectItem):
    __tablename__ = 'folder_share_object_item'
    S3AccessPointName = Column(String, nullable=True)
    __mapper_args__ = {
        "polymorphic_identity": ShareableType.StorageLocation.value
    }

class BucketShareObjectItem(ShareObjectItem):
    __tablename__ = 'bucket_share_object_item'
    __mapper_args__ = {
        "polymorphic_identity": ShareableType.S3Bucket.value
    }
