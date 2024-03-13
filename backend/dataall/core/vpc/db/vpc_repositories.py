import logging

from sqlalchemy import and_

from dataall.base.db import exceptions
from dataall.core.vpc.db.vpc_models import Vpc

log = logging.getLogger(__name__)


class VpcRepository:
    @staticmethod
    def save_network(session, vpc):
        session.add(vpc)
        session.commit()

    @staticmethod
    def delete_network(session, uri) -> bool:
        vpc = VpcRepository.get_vpc_by_uri(session, uri)
        session.delete(vpc)
        session.commit()
        return True

    @staticmethod
    def get_vpc_by_uri(session, vpc_uri) -> Vpc:
        vpc = session.query(Vpc).get(vpc_uri)
        if not vpc:
            raise exceptions.ObjectNotFound('VPC', vpc_uri)
        return vpc

    @staticmethod
    def find_vpc_by_id_environment(session, vpc_id, environment_uri) -> Vpc:
        vpc = session.query(Vpc).filter(and_(Vpc.VpcId == vpc_id, Vpc.environmentUri == environment_uri)).first()
        return vpc

    @staticmethod
    def get_environment_networks(session, environment_uri):
        return session.query(Vpc).filter(Vpc.environmentUri == environment_uri).all()
