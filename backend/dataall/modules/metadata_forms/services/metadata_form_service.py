from functools import wraps

from dataall.base.context import get_context
from dataall.base.db import exceptions, paginate
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.environment.db.environment_repositories import EnvironmentRepository

from dataall.modules.metadata_forms.db.enums import MetadataFormVisibility, MetadataFormUserRoles
from dataall.modules.metadata_forms.db.enums import MetadataFormFieldType
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository


class MetadataFormParamValidationService:
    @staticmethod
    def validate_create_form_params(data):
        visibility = data.get('visibility', MetadataFormVisibility.Team.value)
        if not MetadataFormVisibility.has_value(visibility):
            data['visibility'] = MetadataFormVisibility.Global.value

        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('SamlGroupName')

        if (not data.get('homeEntity')) and (visibility != MetadataFormVisibility.Global.value):
            raise exceptions.RequiredParameter('homeEntity')

        if not data.get('name'):
            raise exceptions.RequiredParameter('name')

    @staticmethod
    def validate_create_field_params(data):
        if 'name' not in data:
            raise exceptions.RequiredParameter('name')
        if 'type' not in data:
            raise exceptions.RequiredParameter('type')

        if data.get('type') == MetadataFormFieldType.GlossaryTerm.value and 'glossaryNodeUri' not in data:
            raise exceptions.RequiredParameter('glossaryNodeUri')


class MetadataFormAccessService:
    @staticmethod
    def is_owner(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return MetadataFormRepository.get_metadata_form_owner(session, uri) in context.groups

    @staticmethod
    def can_perform(action: str):
        def decorator(f):
            @wraps(f)
            def check_permission(*args, **kwds):
                uri = kwds.get('uri')
                if not uri:
                    raise KeyError(f"{f.__name__} doesn't have parameter uri.")

                if MetadataFormAccessService.is_owner(uri):
                    return f(*args, **kwds)
                else:
                    raise exceptions.UnauthorizedOperation(
                        action=action,
                        message=f'User {get_context().username} is not the owner of the metadata form {uri}',
                    )

            return check_permission

        return decorator

    @staticmethod
    def get_user_role(uri):
        if MetadataFormAccessService.is_owner(uri):
            return MetadataFormUserRoles.Owner.value
        else:
            return MetadataFormUserRoles.User.value


class MetadataFormService:
    @staticmethod
    def create_metadata_form(data):
        MetadataFormParamValidationService.validate_create_form_params(data)
        with get_context().db_engine.scoped_session() as session:
            form = MetadataFormRepository.create_metadata_form(session, data)
            return form

    # toDo: add permission check
    @staticmethod
    def get_metadata_form_by_uri(uri):
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.get_metadata_form(session, uri)

    # toDo: deletion logic
    @staticmethod
    @MetadataFormAccessService.can_perform('DELETE')
    def delete_metadata_form_by_uri(uri):
        mf = MetadataFormService.get_metadata_form_by_uri(uri)
        with get_context().db_engine.scoped_session() as session:
            return session.delete(mf)

    @staticmethod
    def paginated_metadata_form_list(filter=None) -> dict:
        context = get_context()
        data = filter if filter is not None else {}
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=MetadataFormRepository.list_metadata_forms(session, filter),
                page=filter.get('page', 1),
                page_size=filter.get('pageSize', 5),
            ).to_dict()

    @staticmethod
    def get_home_entity_name(metadata_form):
        if metadata_form.visibility == MetadataFormVisibility.Team.value:
            return metadata_form.homeEntity
        elif metadata_form.visibility == MetadataFormVisibility.Organization.value:
            with get_context().db_engine.scoped_session() as session:
                return OrganizationRepository.get_organization_by_uri(session, metadata_form.homeEntity).name
        elif metadata_form.visibility == MetadataFormVisibility.Environment.value:
            with get_context().db_engine.scoped_session() as session:
                return EnvironmentRepository.get_environment_by_uri(session, metadata_form.homeEntity).name
        else:
            return ''

    @staticmethod
    def get_metadata_form_fields(uri):
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.get_metadata_form_fields(session, uri)

    @staticmethod
    def get_metadata_form_field_by_uri(uri):
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.get_metadata_form_field_by_uri(session, uri)

    @staticmethod
    @MetadataFormAccessService.can_perform('ADD FIELD')
    def create_metadata_form_field(uri, data):
        MetadataFormParamValidationService.validate_create_field_params(data)
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.create_metadata_form_field(session, uri, data)

    @staticmethod
    @MetadataFormAccessService.can_perform('ADD FIELDS')
    def create_metadata_form_fields(uri, data_arr):
        fields = []
        for data in data_arr:
            fields.append(MetadataFormService.create_metadata_form_field(uri, data))
        return fields

    @staticmethod
    @MetadataFormAccessService.can_perform('DELETE FIELD')
    def delete_metadata_form_field(uri, fieldUri):
        mf = MetadataFormService.get_metadata_form_field_by_uri(fieldUri)
        with get_context().db_engine.scoped_session() as session:
            return session.delete(mf)

    @staticmethod
    @MetadataFormAccessService.can_perform('UPDATE FIELDS')
    def batch_metadata_form_field_update(uri, data):
        for item in data:
            if item.get('metadataFormUri') != uri:
                raise Exception('property metadataFormUri does not match form uri')
            if 'uri' not in item:
                MetadataFormService.create_metadata_form_field(uri, item)
            elif item.get('uri') is not None:
                if item.get('deleted', False):
                    MetadataFormService.delete_metadata_form_field(uri, item['uri'])
                else:
                    MetadataFormService.update_metadata_form_field(uri, item['uri'], item)
        return MetadataFormService.get_metadata_form_fields(uri)

    @staticmethod
    @MetadataFormAccessService.can_perform('UPDATE FIELD')
    def update_metadata_form_field(uri, fieldUri, data):
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.update_metadata_form_field(session, fieldUri, data)
