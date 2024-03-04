import datetime
import json
from enum import Enum
from typing import Dict, Any

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent

from dataall.base.api import appSyncResolver
from dataall.base.db import Base


def todict(obj, parent_obj=None):
    if isinstance(obj, dict):
        # if parent_obj is SQLAlchemy model then don't recurse into dicts and return them as strings
        if isinstance(parent_obj, Base):
            return json.dumps(obj)
        return {k: todict(v, obj) for (k, v) in obj.items()}
    elif isinstance(obj, Enum):
        return obj.name
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif hasattr(obj, "mock_calls"):
        return obj
    elif hasattr(obj, "_ast"):
        return todict(obj._ast(), obj)
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        log.info('hasattr dict %s', hasattr(obj, "__dict__"))
        log.info('__iter__ %s', obj)
        if hasattr(obj, "__dict__"):
            log.info('__dict__ %s', obj.__dict__.items())
        return [todict(v, obj) for v in obj]
    elif hasattr(obj, "__dict__"):
        log.info('__dict__ %s', obj)
        return {k: todict(v, obj) for k, v in obj.__dict__.items() if not callable(v) and not k.startswith('_')}
    else:
        return obj


class dotdict(dict):
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
                source = dotdict(super().source)
            extra_arguments = {
                'context': dotdict(app_context),
                'source': source
            }
            extra_arguments.update(super().arguments)
            return extra_arguments

    response = appSyncResolver.resolve(event=event, context=context, data_model=CustomModel)
    return todict(response)
