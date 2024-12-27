"""
API for request context.
Request context is a storage for associated with the request and should accessible from any part of application
that in the request scope

The class uses Flask's approach to handle request: ThreadLocal
That approach should work fine for AWS Lambdas and local server that uses FastApi app
"""

from dataclasses import dataclass
from typing import List

from dataall.base.db.connection import Engine
from threading import local


_request_storage = local()


@dataclass(frozen=True)
class RequestContext:
    """Contains API for every graphql request"""

    db_engine: Engine
    username: str
    groups: List[str]
    user_id: str


def get_context() -> RequestContext:
    """Retrieves context associated with a request"""
    return _request_storage.context


def set_context(context: RequestContext) -> None:
    """Retrieves context associated with a request"""
    _request_storage.context = context


def dispose_context() -> None:
    """Dispose context after the request completion"""
    _request_storage.context = None
