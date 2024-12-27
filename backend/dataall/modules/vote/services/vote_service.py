"""
A service layer for Votes
Central part for working with Votes
"""

from typing import Dict, Type

from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer
from dataall.modules.vote.db.vote_repositories import VoteRepository

_VOTE_TYPES: Dict[str, Dict[Type[BaseIndexer], str]] = {}


def add_vote_type(target_type: str, indexer: Type[BaseIndexer], permission: str):
    _VOTE_TYPES[target_type] = {'indexer': indexer, 'permission': permission}


def get_vote_type(target_type: str) -> dict[Type[BaseIndexer], str]:
    return _VOTE_TYPES[target_type]


def _session():
    return get_context().db_engine.scoped_session()


class VoteService:
    """
    Encapsulate the logic of interactions with Votes.
    """

    @staticmethod
    def upvote(targetUri: str, targetType: str, upvote: bool):
        context = get_context()
        target_type = get_vote_type(targetType)
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=targetUri,
                permission_name=target_type.get('permission'),
            )
            vote = VoteRepository.upvote(session=session, targetUri=targetUri, targetType=targetType, upvote=upvote)
            target_type.get('indexer').upsert(session, vote.targetUri)
            return vote

    @staticmethod
    def get_vote(targetUri: str, targetType: str):
        with _session() as session:
            return VoteRepository.get_vote(session=session, targetUri=targetUri, targetType=targetType)

    @staticmethod
    def count_upvotes(targetUri: str, targetType: str):
        with _session() as session:
            return VoteRepository.count_upvotes(session=session, targetUri=targetUri, target_type=targetType)
