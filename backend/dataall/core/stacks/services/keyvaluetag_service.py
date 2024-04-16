from typing import List


from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTagRepository
from dataall.core.stacks.db.stack_models import KeyValueTag
from dataall.base.db.exceptions import RequiredParameter, UnauthorizedOperation
from dataall.base.context import get_context
from dataall.core.stacks.db.target_type_repositories import TargetType


class KeyValueTagParamValidationService:
    @staticmethod
    def validate_update_param(uri: str, data: dict):
        if not uri:
            raise RequiredParameter('targetUri')
        if not data:
            raise RequiredParameter('data')
        if not data.get('targetType'):
            raise RequiredParameter('targetType')

    @staticmethod
    def verify_target_type_and_uri(target_type, target_uri):
        if not target_uri:
            raise RequiredParameter('targetUri')
        if not target_type:
            raise RequiredParameter('targetType')


class KeyValueTagService:
    @staticmethod
    def update_key_value_tags(uri: str, data: dict = None) -> List[KeyValueTag]:
        KeyValueTagParamValidationService.validate_update_param(uri, data)
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=uri,
                permission_name=TargetType.get_resource_update_permission_name(data['targetType']),
            )

            tag_keys = [tag['key'].lower() for tag in data.get('tags', [])]
            if tag_keys and len(tag_keys) != len(set(tag_keys)):
                raise UnauthorizedOperation(
                    action='SAVE_KEY_VALUE_TAGS',
                    message='Duplicate tag keys found. Please note that Tag keys are case insensitive',
                )

            tags = []
            KeyValueTagRepository.delete_key_value_tags(session, uri, data['targetType'])
            for tag in data.get('tags'):
                kv_tag: KeyValueTag = KeyValueTag(
                    targetUri=uri,
                    targetType=data['targetType'],
                    key=tag['key'],
                    value=tag['value'],
                    cascade=tag['cascade'],
                )
                tags.append(kv_tag)
                session.add(kv_tag)

            return tags

    @staticmethod
    def list_key_value_tags(target_uri, target_type) -> dict:
        KeyValueTagParamValidationService.verify_target_type_and_uri(target_uri, target_type)
        context = get_context()
        with context.db_engine.scoped_session() as session:
            ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=target_uri,
                permission_name=TargetType.get_resource_read_permission_name(target_type),
            )
            return KeyValueTagRepository.find_key_value_tags(session, target_uri, target_type)
