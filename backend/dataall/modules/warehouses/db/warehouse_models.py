"""ORM models for Warehouses"""

import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey

from dataall.base.db import Base
from dataall.base.db import utils


class WarehouseConnection(Base):
    """Describes ORM model for warehouse connections"""

    __tablename__ = 'warehouse_connection'
    # environmentUri = Column(String, ForeignKey("environment.environmentUri"), nullable=False)
    connectionUri = Column(String, primary_key=True, default=utils.uuid('warehouse_connection'))
    # AWSAccountId = Column(String, nullable=False)
    # region = Column(String, default='eu-west-1')
    SamlAdminGroupName = Column(String, nullable=False)
    name = Column(String, nullable=False)
    warehouseId = Column(String, nullable=False)
    warehouseType = Column(String, nullable=False)
    connectionType = Column(String, nullable=False)
    connectionDetails = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)


class WarehouseConsumer(Base):
    """Describes ORM model for warehouse consumers"""

    __tablename__ = 'warehouse_consumer'
    # environmentUri = Column(String, ForeignKey("environment.environmentUri"), nullable=False)
    consumerUri = Column(String, primary_key=True, default=utils.uuid('warehouse_consumer'))
    # AWSAccountId = Column(String, nullable=False)
    # region = Column(String, default='eu-west-1')
    SamlAdminGroupName = Column(String, nullable=False)
    name = Column(String, nullable=False)
    warehouseId = Column(String, nullable=False)
    warehouseType = Column(String, nullable=False)
    consumerType = Column(String, nullable=False)
    consumerDetails = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
