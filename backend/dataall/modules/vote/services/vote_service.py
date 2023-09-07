"""
A service layer for Votes
Central part for working with Votes
"""
from typing import Dict, Type
from dataall.base.context import get_context
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer
from dataall.modules.vote.db.vote_repositories import VoteRepository

_VOTE_TYPES: Dict[str, Type[BaseIndexer]] = {}


def add_vote_type(target_type: str, indexer: Type[BaseIndexer]):
    _VOTE_TYPES[target_type] = indexer


def _session():
    return get_context().db_engine.scoped_session()


class VoteService:
    """
    Encapsulate the logic of interactions with Votes.
    """

    @staticmethod
    def upvote(targetUri: str, targetType: str, upvote: bool):
        with _session() as session:
            vote = VoteRepository.upvote(
                session=session,
                targetUri=targetUri,
                targetType=targetType,
                upvote=upvote
            )
            _VOTE_TYPES[vote.targetType].upsert(session, vote.targetUri)
            return vote

    @staticmethod
    def get_vote(targetUri: str, targetType: str):
        with _session() as session:
            return VoteRepository.get_vote(
                session=session,
                targetUri=targetUri,
                targetType=targetType
            )

    @staticmethod
    def count_upvotes(targetUri: str, targetType: str):
        with _session() as session:
            return VoteRepository.count_upvotes(
                session=session,
                targetUri=targetUri,
                target_type=targetType
            )
