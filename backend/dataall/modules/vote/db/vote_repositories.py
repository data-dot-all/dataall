import logging
from datetime import datetime

from dataall.modules.vote.db import vote_models as models
from dataall.base.context import get_context

logger = logging.getLogger(__name__)


class VoteRepository:
    @staticmethod
    def get_vote(session, targetUri, targetType) -> [models.Vote]:
        return (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == targetUri,
                models.Vote.targetType == targetType,
                models.Vote.username == get_context().username,
            )
            .first()
        )

    @staticmethod
    def upvote(session, targetUri: str, targetType: str, upvote: bool) -> [models.Vote]:
        vote: models.Vote = (
            session.query(models.Vote)
            .filter(
                models.Vote.username == get_context().username,
                models.Vote.targetUri == targetUri,
                models.Vote.targetType == targetType,
            )
            .first()
        )
        if vote:
            vote.upvote = upvote
            vote.updated = datetime.now()

        else:
            vote: models.Vote = models.Vote(
                username=get_context().username,
                targetUri=targetUri,
                targetType=targetType,
                upvote=upvote,
            )
            session.add(vote)

        session.commit()
        return vote

    @staticmethod
    def count_upvotes(session, targetUri, target_type) -> dict:
        return (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == targetUri,
                models.Vote.targetType == target_type,
                models.Vote.upvote == True,
            )
            .count()
        )

    @staticmethod
    def delete_votes(session, target_uri, target_type) -> [models.Vote]:
        return (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == target_uri,
                models.Vote.targetType == target_type,
            )
            .delete()
        )
