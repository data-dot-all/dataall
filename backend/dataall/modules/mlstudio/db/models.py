"""ORM models for sagemaker studio"""

from sqlalchemy import Column, String, Integer, ForeignKey

from dataall.db import Base
from dataall.db import Resource, utils


class MLStudio(Resource, Base):
    """Describes ORM model for sagemaker ML Studio"""

    __tablename__ = '....'

