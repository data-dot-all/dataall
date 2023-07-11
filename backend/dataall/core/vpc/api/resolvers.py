import logging

from dataall.api.context import Context
from dataall.db.api import Vpc

log = logging.getLogger(__name__)


def create_network(context: Context, source, input):
    with context.engine.scoped_session() as session:
        vpc = Vpc.create_network(
            session=session,
            uri=input['environmentUri'],
            admin_group=input['SamlGroupName'],
            data=input,
        )
    return vpc


def get_network(context: Context, source, vpcUri: str = None):
    with context.engine.scoped_session() as session:
        return Vpc.get_network(session=session, uri=vpcUri)


def delete_network(context: Context, source, vpcUri=None):
    with context.engine.scoped_session() as session:
        return Vpc.delete(session=session, uri=vpcUri)
