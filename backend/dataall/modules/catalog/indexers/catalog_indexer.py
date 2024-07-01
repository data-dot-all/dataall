from abc import ABC
from typing import List


class CatalogIndexer(ABC):
    _INDEXERS: List['CatalogIndexer'] = []

    def __init__(self):
        CatalogIndexer._INDEXERS.append(self)

    @staticmethod
    def all():
        return CatalogIndexer._INDEXERS

    def index(self, session) -> List[str]:
        raise NotImplementedError('index is not implemented')
