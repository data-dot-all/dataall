from typing import Dict, Type
from dataall.base.db import exceptions
from dataall.modules.vote.services.vote_service import VoteService
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer

_VOTE_TYPES: Dict[str, Type[BaseIndexer]] = {}


def _required_param(param, name):
    if not param:
        raise exceptions.RequiredParameter(name)


def upvote(context, source, input=None):
    if not input:
        raise exceptions.RequiredParameter('data')
    _required_param(param=input['targetUri'], name='URI')
    _required_param(param=input['targetType'], name='targetType')
    _required_param(param=input['upvote'], name='Upvote')
    return VoteService.upvote(
        targetUri=input['targetUri'],
        targetType=input['targetType'],
        upvote=input['upvote']
    )


def get_vote(context, source, targetUri: str = None, targetType: str = None):
    _required_param(param=targetUri, name='URI')
    _required_param(param=targetType, name='targetType')
    return VoteService.get_vote(
        target_uri=targetUri,
        target_type=targetType
    )


def count_upvotes(
    context, source, targetUri: str = None, targetType: str = None
):
    _required_param(param=targetUri, name='URI')
    _required_param(param=targetType, name='targetType')
    return VoteService.count_upvotes(targetUri=targetUri, targetType=targetType)
