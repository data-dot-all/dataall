from dataall.base.context import get_context
from dataall.base.db import exceptions, paginate
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.environment.db.environment_repositories import EnvironmentRepository

from dataall.modules.metadata_forms.db.enums import MetadataFormVisibility
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository


class MetadataFormParamValidationService:
    @staticmethod
    def validate_create_form_params(data):
        visibility = data.get('visibility', MetadataFormVisibility.Team.value)
        if not MetadataFormVisibility.has_value(visibility):
            data['visibility'] = MetadataFormVisibility.Team.value

        if 'SamlGroupName' not in data:
            raise exceptions.RequiredParameter('SamlGroupName')

        if 'homeEntity' not in data and (
            visibility == MetadataFormVisibility.Organization.value
            or visibility == MetadataFormVisibility.Environment.value
        ):
            raise exceptions.RequiredParameter('homeEntity')

        if 'name' not in data:
            data['name'] = 'New Form'


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

    # toDo: add permission check
    # toDo: deletion logic
    @staticmethod
    def delete_metadata_form_by_uri(uri):
        mf = MetadataFormService.get_metadata_form_by_uri(uri)
        with get_context().db_engine.scoped_session() as session:
            return session.delete(mf)

    @staticmethod
    def paginated_metadata_form_list(data=None) -> dict:
        context = get_context()
        data = data if data is not None else {}
        with context.db_engine.scoped_session() as session:
            return paginate(
                query=MetadataFormRepository.list_metadata_forms(session, filter),
                page=data.get('page', 1),
                page_size=data.get('pageSize', 5),
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
