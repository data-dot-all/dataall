import logging
from datetime import datetime

from .. import exceptions, models

logger = logging.getLogger(__name__)


class Vote:
    @staticmethod
    def upvote(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> [models.Vote]:

        if not uri:
            raise exceptions.RequiredParameter("targetUri")
        if not data:
            raise exceptions.RequiredParameter("data")
        if not data.get("targetType"):
            raise exceptions.RequiredParameter("targetType")
        if "upvote" not in data:
            raise exceptions.RequiredParameter("upvote")

        vote: models.Vote = (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == uri,
                models.Vote.targetType == data["targetType"],
            )
            .first()
        )
        if vote:
            vote.upvote = data["upvote"]
            vote.updated = datetime.now()

        else:
            vote: models.Vote = models.Vote(
                username=username,
                targetUri=uri,
                targetType=data["targetType"],
                upvote=data["upvote"],
            )
            session.add(vote)

        session.commit()
        return vote

    @staticmethod
    def count_upvotes(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return (
            session.query(models.Vote)
            .filter(
                models.Vote.targetUri == uri,
                models.Vote.targetType == data["targetType"],
                models.Vote.upvote == True,
            )
            .count()
        )

    @staticmethod
    def get_vote(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return Vote.find_vote(session, uri, data["targetType"])

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
