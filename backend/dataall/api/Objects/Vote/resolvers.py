from .... import db
from ....api.context import Context
from dataall.searchproxy.indexers import DatasetIndexer, DashboardIndexer


def count_upvotes(
    context: Context, source, targetUri: str = None, targetType: str = None
):
    with context.engine.scoped_session() as session:
        return db.api.Vote.count_upvotes(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=targetUri,
            data={'targetType': targetType},
            check_perm=True,
        )


def upvote(context: Context, source, input=None):
    with context.engine.scoped_session() as session:
        vote = db.api.Vote.upvote(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['targetUri'],
            data=input,
            check_perm=True,
        )
        reindex(session, context.es, vote)
        return vote


def reindex(session, es, vote):
    if vote.targetType == 'dataset':
        DatasetIndexer.upsert(session=session, dataset_uri=vote.targetUri)
    elif vote.targetType == 'dashboard':
        DashboardIndexer.upsert(session=session, dashboard_uri=vote.targetUri)


def get_vote(context: Context, source, targetUri: str = None, targetType: str = None):
    with context.engine.scoped_session() as session:
        return db.api.Vote.get_vote(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=targetUri,
            data={'targetType': targetType},
            check_perm=True,
        )
