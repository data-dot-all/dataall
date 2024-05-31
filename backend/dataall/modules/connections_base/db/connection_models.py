"""The package contains the database models that are related to the environment connections"""
from sqlalchemy import Column, Enum, String, ForeignKey
from dataall.base.db import Resource, Base, utils

from dataall.modules.connections_base.api.enums import ConnectionType


class Connection(Resource, Base):
    __tablename__ = 'connection'
    environmentUri = Column(String, ForeignKey('environment.environmentUri'), nullable=False)
    connectionUri = Column(String, primary_key=True, default=utils.uuid('connection'))
    connectionType = Column(Enum(ConnectionType), nullable=False, default=ConnectionType.Redshift)
    SamlGroupName = Column(String, nullable=False)

    __mapper_args__ = {'polymorphic_identity': 'connection', 'polymorphic_on': connectionType}

