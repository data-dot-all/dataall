import logging

from sqlalchemy import and_, or_

from dataall.base.db import exceptions
from dataall.core.vpc.db.vpc_models import Vpc
from dataall.base.utils.naming_convention import NamingConventionPattern, NamingConventionService

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

    @staticmethod
    def query_environment_networks(session, uri, filter):
        query = session.query(Vpc).filter(
            Vpc.environmentUri == uri,
        )
        if filter.get('term'):
            term = filter.get('term')
            query = query.filter(
                or_(
                    Vpc.label.ilike('%' + term + '%'),
                    Vpc.VpcId.ilike('%' + term + '%'),
                    Vpc.tags.contains(
                        f'{{{NamingConventionService(pattern=NamingConventionPattern.DEFAULT_SEARCH, target_label=term).sanitize()}}}'
                    ),
                )
            )
        return query.order_by(Vpc.label)
