import logging

from . import TargetType
from .resource_policy import ResourcePolicy
from .. import exceptions
from .. import models

logger = logging.getLogger(__name__)


class KeyValueTag:
    @staticmethod
    def update_key_value_tags(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> [models.KeyValueTag]:

        if not uri:
            raise exceptions.RequiredParameter('targetUri')
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('targetType'):
            raise exceptions.RequiredParameter('targetType')

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=username,
            groups=groups,
            resource_uri=uri,
            permission_name=TargetType.get_resource_update_permission_name(
                data['targetType']
            ),
        )

        tag_keys = [tag['key'].lower() for tag in data.get('tags', [])]
        if tag_keys and len(tag_keys) != len(set(tag_keys)):
            raise exceptions.UnauthorizedOperation(
                action='SAVE_KEY_VALUE_TAGS',
                message='Duplicate tag keys found. Please note that Tag keys are case insensitive',
            )

        tags = []
        session.query(models.KeyValueTag).filter(
            models.KeyValueTag.targetUri == uri,
            models.KeyValueTag.targetType == data['targetType'],
        ).delete()
        for tag in data.get('tags'):
            kv_tag: models.KeyValueTag = models.KeyValueTag(
                targetUri=uri,
                targetType=data['targetType'],
                key=tag['key'],
                value=tag['value'],
                cascade=tag['cascade']
            )
            tags.append(kv_tag)
            session.add(kv_tag)

        return tags

    @staticmethod
    def update_cascading_key_value_tag(
        session,
        username: str,
        groups: [str],
        uri: str,
        targetUri: str,
        targetType: str,
        cascade: bool = False,
        check_perm: bool = False,
    ) -> [models.KeyValueTag]:

        if not uri:
            raise exceptions.RequiredParameter('tagUri')
        if not cascade:
            raise exceptions.RequiredParameter('cascade')
        if not targetUri:
            raise exceptions.RequiredParameter('targetUri')
        if not targetType:
            raise exceptions.RequiredParameter('targetType')

        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=username,
            groups=groups,
            resource_uri=targetUri,
            permission_name=TargetType.get_resource_update_permission_name(
                targetType
            ),
        )

        tag = KeyValueTag.get_tag_by_uri(session=session, uri=uri)
        tag.cascade = cascade
        session.commit()

        return True

    @staticmethod
    def get_tag_by_uri(session, uri) -> models.KeyValueTag:
        if not uri:
            raise exceptions.RequiredParameter('tagUri')
        tag: models.KeyValueTag = session.query(models.KeyValueTag).get(uri)

        if not tag:
            raise exceptions.ObjectNotFound(models.KeyValueTag.__name__, uri)
        return tag

    @staticmethod
    def list_key_value_tags(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=username,
            groups=groups,
            resource_uri=uri,
            permission_name=TargetType.get_resource_read_permission_name(
                data['targetType']
            ),
        )
        return KeyValueTag.find_key_value_tags(session, uri, data['targetType'])

    @staticmethod
    def find_key_value_tags(session, target_uri, target_type) -> [models.KeyValueTag]:
        return (
            session.query(models.KeyValueTag)
            .filter(
                models.KeyValueTag.targetUri == target_uri,
                models.KeyValueTag.targetType == target_type,
            )
            .all()
        )

    @staticmethod
    def delete_key_value_tags(session, target_uri, target_type):
        return (
            session.query(models.KeyValueTag)
            .filter(
                models.KeyValueTag.targetUri == target_uri,
                models.KeyValueTag.targetType == target_type,
            )
            .delete()
        )
