import logging

from ....api.context import Context
from ....db.api import Vpc

log = logging.getLogger(__name__)


def create_network(context: Context, source, input):
    with context.engine.scoped_session() as session:
        vpc = Vpc.create_network(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['environmentUri'],
            data=input,
            check_perm=True,
        )
    return vpc


def delete_network(context: Context, source, vpcUri=None):
    with context.engine.scoped_session() as session:
        return Vpc.delete(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=vpcUri,
            data=None,
            check_perm=True,
        )
