import logging

from dataall.core.stacks.db.stack_models import KeyValueTag
from typing import List

logger = logging.getLogger(__name__)


class KeyValueTagRepository:
    @staticmethod
    def find_key_value_tags(session, target_uri, target_type) -> List[KeyValueTag]:
        return (
            session.query(KeyValueTag)
            .filter(
                KeyValueTag.targetUri == target_uri,
                KeyValueTag.targetType == target_type,
            )
            .all()
        )

    @staticmethod
    def find_environment_cascade_key_value_tags(session, target_uri) -> List[KeyValueTag]:
        return (
            session.query(KeyValueTag)
            .filter(
                KeyValueTag.targetUri == target_uri,
                KeyValueTag.targetType == 'environment',
                KeyValueTag.cascade.is_(True),
            )
            .all()
        )

    @staticmethod
    def delete_key_value_tags(session, target_uri, target_type):
        return (
            session.query(KeyValueTag)
            .filter(
                KeyValueTag.targetUri == target_uri,
                KeyValueTag.targetType == target_type,
            )
            .delete()
        )
