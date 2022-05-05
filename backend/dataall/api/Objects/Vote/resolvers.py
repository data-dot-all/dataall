from .... import db
from ....api.context import Context
from ....searchproxy.indexers import upsert_dashboard, upsert_dataset


def count_upvotes(context: Context, source, targetUri: str = None, targetType: str = None):
    with context.engine.scoped_session() as session:
        return db.api.Vote.count_upvotes(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=targetUri,
            data={"targetType": targetType},
            check_perm=True,
        )


def upvote(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        vote = db.api.Vote.upvote(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input["targetUri"],
            data=input,
            check_perm=True,
        )
        reindex(session, context.es, vote)
        return vote


def reindex(session, es, vote):
    if vote.targetType == "dataset":
        upsert_dataset(session=session, es=es, datasetUri=vote.targetUri)
    elif vote.targetType == "dashboard":
        upsert_dashboard(session=session, es=es, dashboardUri=vote.targetUri)


def get_vote(context: Context, source, targetUri: str = None, targetType: str = None):
    with context.engine.scoped_session() as session:
        return db.api.Vote.get_vote(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=targetUri,
            data={"targetType": targetType},
            check_perm=True,
        )
