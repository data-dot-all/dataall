import datetime
from enum import Enum
from typing import Dict, Any

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent

from dataall.base.api import appSyncResolver


def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif isinstance(obj, Enum):
        return obj.name
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif hasattr(obj, "mock_calls"):
        return obj
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def handler(event, context, app_context):
    class MyCustomModel(AppSyncResolverEvent):
        @property
        def arguments(self) -> Dict[str, Any]:
            source = None
            if super().source:
                source = dotdict(super().source)
            extra_arguments = {
                'context': dotdict(app_context),
                'source': source
            }
            extra_arguments.update(super().arguments)
            return extra_arguments

    response = appSyncResolver.resolve(event=event, context=context, data_model=MyCustomModel)
    return todict(response)
