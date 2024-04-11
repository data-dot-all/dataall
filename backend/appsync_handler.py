import json
import logging
from typing import Dict, Any

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Query

from dataall.base.api import appSyncResolver
from dataall.base.db import Base

logger = logging.getLogger()
logger.setLevel('DEBUG')
log = logging.getLogger(__name__)


def sqa_query_encoder(obj: Query):
    log.warning('raw query returned by resolver %s', obj)
    return jsonable_encoder(obj.all(), custom_encoder=CUSTOM_ENCODERS)


def sqa_base_encoder(obj: Base):
    return jsonable_encoder(
        {k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in vars(obj).items()}, custom_encoder=CUSTOM_ENCODERS
    )


CUSTOM_ENCODERS = {
    # Convert SQA JSON columns to str for compatibility with GQL
    Base: sqa_base_encoder,
    # Some resolvers return raw un-executed Query
    Query: sqa_query_encoder,
}


def todict(obj):
    return jsonable_encoder(obj, custom_encoder=CUSTOM_ENCODERS)


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def handler(event, context, app_context):
    class CustomModel(AppSyncResolverEvent):
        @property
        def arguments(self) -> Dict[str, Any]:
            """
            add context,source in the arguments to make the calls compatible with the current resolvers
            """
            source = None
            if super().source:
                source = DotDict(super().source)
            extra_arguments = {'context': DotDict(app_context), 'source': source}
            extra_arguments.update(super().arguments)
            return extra_arguments

    response = appSyncResolver.resolve(event=event, context=context, data_model=CustomModel)
    log.info('raw appsync response %s', response)
    return todict(response)
