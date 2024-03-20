import logging

from dataall.core.stacks.db import stack_models as models
from dataall.base.db import exceptions

log = logging.getLogger(__name__)


class Stack:
    @staticmethod
    def get_stack_by_target_uri(session, target_uri):
        stack = Stack.find_stack_by_target_uri(session, target_uri)
        if not stack:
            raise exceptions.ObjectNotFound('Stack', target_uri)
        return stack

    @staticmethod
    def find_stack_by_target_uri(session, target_uri):
        stack: models.Stack = session.query(models.Stack).filter(models.Stack.targetUri == target_uri).first()
        return stack

    @staticmethod
    def get_stack_by_uri(session, stack_uri):
        stack = Stack.find_stack_by_uri(session, stack_uri)
        if not stack:
            raise exceptions.ObjectNotFound('Stack', stack_uri)
        return stack

    @staticmethod
    def find_stack_by_uri(session, stack_uri):
        stack: models.Stack = session.query(models.Stack).get(stack_uri)
        return stack
