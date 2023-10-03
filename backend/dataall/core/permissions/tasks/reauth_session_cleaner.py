import logging
import os
import sys
from operator import and_
import datetime

from dataall.base.db import get_engine
from dataall.core.permissions.db.permission_models import ReAuthSession

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def clean_expired_reauth_sessions(engine):
    now = datetime.datetime.utcnow()
    with engine.scoped_session() as session:
        reauth_sessions = session.query(ReAuthSession).all()
        log.info(f'Found {len(reauth_sessions)} reauth sessions')
        reauth_session: ReAuthSession
        try:
            for reauth_session in reauth_sessions:
                expiry_time = reauth_session.created + datetime.timedelta(minutes=int(reauth_session.ttl))
                if now > expiry_time:
                    session.delete(reauth_session)
                    session.commit()
        except Exception as e:
            log.error(
                f'Failed to check expiry times for reauth sessions '
                f'due to: {e}'
            )
        return True


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    clean_expired_reauth_sessions(engine=ENGINE)
