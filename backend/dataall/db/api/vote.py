import logging
from datetime import datetime

from .. import exceptions
from .. import models
from dataall.base.context import get_context

logger = logging.getLogger(__name__)


class Vote:
    @staticmethod
    def upvote(session, uri: str, data: dict = None) -> [models.Vote]:
        if not uri:
            raise exceptions.RequiredParameter('targetUri')
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('targetType'):
            raise exceptions.RequiredParameter('targetType')
        if 'upvote' not in data:
            raise exceptions.RequiredParameter('upvote')

        vote: models.Vote = (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == uri,
                models.Vote.targetType == data['targetType'],
            )
            .first()
        )
        if vote:
            vote.upvote = data['upvote']
            vote.updated = datetime.now()

        else:
            vote: models.Vote = models.Vote(
                username=get_context().username,
                targetUri=uri,
                targetType=data['targetType'],
                upvote=data['upvote'],
            )
            session.add(vote)

        session.commit()
        return vote

    @staticmethod
    def count_upvotes(session, uri, target_type) -> dict:
        return (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == uri,
                models.Vote.targetType == target_type,
                models.Vote.upvote == True,
            )
            .count()
        )

    @staticmethod
    def find_vote(session, target_uri, target_type) -> [models.Vote]:
        return (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == target_uri,
                models.Vote.targetType == target_type,
            )
            .first()
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
