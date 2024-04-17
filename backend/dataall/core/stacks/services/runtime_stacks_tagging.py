import os
import typing
from enum import Enum

from aws_cdk import Stack, Tags

from dataall.base import db
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTagRepository
from dataall.core.stacks.db.stack_models import KeyValueTag as KeyValueTagModel


# Tag keys for Stacks
class StackTagName(Enum):
    def __str__(self):
        return str(self.value)

    CREATOR = 'Creator'
    ORGANISATION = 'Organization'
    ENVIRONMENT = 'Environment'
    TARGET = 'Target'
    TEAM = 'Team'
    DATAALL = 'dataall'


# Tags adding class
class TagsUtil:
    def __init__(self, stack):
        self.stack = stack

    @classmethod
    def add_tags(cls, stack: Stack, model, target_type) -> [tuple]:
        """
        A class method that adds tags to a Stack
        """

        # Get the list of tags to be added from the tag factory
        stack_tags_to_add = cls.tag_factory(stack, model, target_type)

        # Add the tags to the Stack
        for tag in stack_tags_to_add:
            Tags.of(stack).add(str(tag[0]), str(tag[1]))

        return stack_tags_to_add

    @classmethod
    def tag_factory(cls, stack: Stack, model_name, target_type) -> typing.List[typing.Tuple]:
        """
        A class method that returns tags to be added to a Stack (based on Stack type)
        """

        _stack_tags = []

        engine = cls.get_engine()

        # Initialize references to stack's environment and organisation
        with engine.scoped_session() as session:
            target_stack = cls.get_target(session, stack, model_name)
            environment = cls.get_environment(session, target_stack)
            organisation = cls.get_organization(session, environment)
            key_value_tags: [KeyValueTagModel] = cls.get_model_key_value_tags(session, stack, target_type)
            cascaded_tags: [KeyValueTagModel] = cls.get_environment_cascade_key_value_tags(
                session, environment.environmentUri
            )

        # Build a list of tuples with tag keys and values based on the collected up to this point
        # ex. target_stack, organisation etc.
        _common_stack_tags = [
            (StackTagName.CREATOR.value, target_stack.owner),
            (
                StackTagName.ORGANISATION.value,
                organisation.name + '_' + organisation.organizationUri,
            ),
            (
                StackTagName.ENVIRONMENT.value,
                environment.name + '_' + environment.environmentUri,
            ),
            (
                StackTagName.TEAM.value,
                (
                    target_stack.SamlGroupName
                    if hasattr(target_stack, 'SamlGroupName')
                    else target_stack.SamlAdminGroupName
                ),
            ),
            (
                StackTagName.TARGET.value,
                model_name.__name__ + '_' + stack.target_uri,
            ),
            (
                StackTagName.DATAALL.value,
                'true',
            ),
        ]

        # Build the final tag list with common tags
        _stack_tags.extend(_common_stack_tags)

        # ..and any additional key value tags
        _stack_tags.extend(key_value_tags)

        # .. and cascade tags inherited form the environment
        _stack_tags.extend(cascaded_tags)

        # Duplicate tag keys are not allowed on CloudFormation. Also Tag keys are case insensitive
        _stack_tags = list(cls.remove_duplicate_tag_keys(_stack_tags).values())

        return _stack_tags

    @classmethod
    def get_engine(cls):
        envname = os.environ.get('envname', 'local')
        engine = db.get_engine(envname=envname)
        return engine

    @classmethod
    def get_target(cls, session, stack, model_name):
        return session.query(model_name).get(stack.target_uri)

    @classmethod
    def get_organization(cls, session, environment):
        organisation = OrganizationRepository.get_organization_by_uri(session, environment.organizationUri)
        return organisation

    @classmethod
    def get_environment(cls, session, target_stack):
        environment: Environment = EnvironmentService.get_environment_by_uri(session, target_stack.environmentUri)
        return environment

    @classmethod
    def get_model_key_value_tags(cls, session, stack, target_type):
        return [
            (kv.key, kv.value)
            for kv in KeyValueTagRepository.find_key_value_tags(
                session,
                stack.target_uri,
                target_type,
            )
        ]

    @classmethod
    def get_environment_cascade_key_value_tags(cls, session, environmentUri):
        return [
            (kv.key, kv.value)
            for kv in KeyValueTagRepository.find_environment_cascade_key_value_tags(
                session,
                environmentUri,
            )
        ]

    @classmethod
    def remove_duplicate_tag_keys(cls, _stack_tags):
        compare_dict = dict()
        results_dict = dict()
        for key, value in reversed(_stack_tags):
            if key.lower() not in compare_dict:  # we see this key for the first time
                compare_dict[key.lower()] = (key, value)
                results_dict[key] = (key, value)
        return results_dict
