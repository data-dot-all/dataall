from abc import ABC
from typing import List


class StackFinder(ABC):
    _FINDERS: List['StackFinder'] = []

    @staticmethod
    def all():
        return StackFinder._FINDERS

    def __init__(self):
        StackFinder._FINDERS.append(self)

    def find_stack_uris(self, session) -> List[str]:
        """Finds stacks to update"""
        raise NotImplementedError('find_stack_uris is not implemented')
