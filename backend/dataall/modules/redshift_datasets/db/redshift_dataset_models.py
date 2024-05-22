from sqlalchemy import Boolean, Column, String, ForeignKey
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.services.datasets_enums import DatasetType


class RedshiftDataset(DatasetBase):
    __tablename__ = 'redshift_dataset'
    datasetUri = Column(String, ForeignKey('dataset.datasetUri'), primary_key=True)
    # TODO ADD REDSHIFT FIELDS

    __mapper_args__ = {
        'polymorphic_identity': DatasetType.Redshift,
    }
