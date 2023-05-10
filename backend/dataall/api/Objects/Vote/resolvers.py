from typing import Dict, Type

from dataall import db
from dataall.api.context import Context
from dataall.searchproxy.indexers import DashboardIndexer
from dataall.searchproxy.base_indexer import BaseIndexer

_VOTE_TYPES: Dict[str, Type[BaseIndexer]] = {}


def add_vote_type(target_type: str, indexer: Type[BaseIndexer]):
    _VOTE_TYPES[target_type] = indexer


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

        _VOTE_TYPES[vote.targetType].upsert(session, vote.targetUri)
        return vote


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


# TODO should migrate after into the Dashboard module
add_vote_type("dashboard", DashboardIndexer)
