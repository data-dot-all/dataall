from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.modules.feed.api.registry import FeedRegistry
from dataall.modules.feed.services.feed_service import Feed, FeedService


def _required_uri(uri):
    if not uri:
        raise exceptions.RequiredParameter('URI')


def _required_type(type):
    if not type:
        raise exceptions.RequiredParameter('TargetType')


def get_feed(
    context: Context,
    source,
    targetUri: str = None,
    targetType: str = None,
):
    _required_uri(targetUri)
    _required_type(targetType)
    return FeedService.get_feed(targetUri=targetUri, targetType=targetType)


def post_feed_message(
    context: Context,
    source,
    targetUri: str = None,
    targetType: str = None,
    input: dict = None,
):
    return FeedService.post_feed_message(targetUri=targetUri, targetType=targetType, content=input.get('content'))


def resolve_feed_target_type(obj, *_):
    return FeedRegistry.find_target(obj)


def resolve_feed_messages(context: Context, source: Feed, filter: dict = None):
    _required_uri(source.targetUri)
    if not filter:
        filter = {}
    return FeedService.list_feed_messages(targetUri=source.targetUri, targetType=source.targetType, filter=filter)
