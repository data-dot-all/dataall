import logging

from dataall.base.context import get_context
from dataall.core.environment.db.models import Environment
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.stacks.db import stack_models as models
from dataall.core.stacks.db.target_type import TargetType
from dataall.base.db import exceptions
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

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
        environment: Environment = session.query(Environment).get(
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
        uri: str,
        target_type: str
    ) -> [models.Stack]:

        if not uri:
            raise exceptions.RequiredParameter('targetUri')
        if not target_type:
            raise exceptions.RequiredParameter('targetType')

        context = get_context()
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=uri,
            permission_name=TargetType.get_resource_update_permission_name(
                target_type
            ),
        )
        stack = Stack.get_stack_by_target_uri(session, target_uri=uri)
        return stack
