from typing import Dict, Type

from dataall.core.vote.db.vote import Vote
from dataall.searchproxy.base_indexer import BaseIndexer

_VOTE_TYPES: Dict[str, Type[BaseIndexer]] = {}


def add_vote_type(target_type: str, indexer: Type[BaseIndexer]):
    _VOTE_TYPES[target_type] = indexer


def count_upvotes(
    context, source, targetUri: str = None, targetType: str = None
):
    with context.engine.scoped_session() as session:
        return Vote.count_upvotes(
            session=session,
            uri=targetUri,
            target_type=targetType
        )


def upvote(context, source, input=None):
    with context.engine.scoped_session() as session:
        vote = Vote.upvote(
            session=session,
            uri=input['targetUri'],
            data=input,
        )

        _VOTE_TYPES[vote.targetType].upsert(session, vote.targetUri)
        return vote


def get_vote(context, source, targetUri: str = None, targetType: str = None):
    with context.engine.scoped_session() as session:
        return Vote.find_vote(
            session=session,
            target_uri=targetUri,
            target_type=targetType
        )
