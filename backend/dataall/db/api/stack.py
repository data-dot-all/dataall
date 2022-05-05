import logging

from ...utils.naming_convention import (NamingConventionPattern,
                                        NamingConventionService)
from .. import exceptions, models
from . import ResourcePolicy, TargetType

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
        stack: models.Stack = (
            session.query(models.Stack)
            .filter(models.Stack.targetUri == target_uri)
            .first()
        )
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

    @staticmethod
    def create_stack(
        session, environment_uri, target_label, target_uri, target_type, payload=None
    ) -> models.Stack:
        environment: models.Environment = session.query(models.Environment).get(
            environment_uri
        )
        if not environment:
            raise exceptions.ObjectNotFound('Environment', environment_uri)

        stack = models.Stack(
            targetUri=target_uri,
            accountid=environment.AwsAccountId,
            region=environment.region,
            stack=target_type,
            payload=payload,
            name=NamingConventionService(
                target_label=target_type,
                target_uri=target_uri,
                pattern=NamingConventionPattern.DEFAULT,
                resource_prefix=environment.resourcePrefix,
            ).build_compliant_name(),
        )
        session.add(stack)
        session.commit()
        return stack

    @staticmethod
    def update_stack(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> [models.Stack]:

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
        stack = Stack.get_stack_by_target_uri(session, target_uri=uri)
        return stack
