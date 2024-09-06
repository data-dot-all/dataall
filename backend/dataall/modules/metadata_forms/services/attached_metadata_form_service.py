from dataall.base.context import get_context
from dataall.base.db import exceptions, paginate
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyValidationService
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository
from dataall.modules.metadata_forms.services.metadata_form_access_service import MetadataFormAccessService


class AttachedMetadataFormValidationService:
    @staticmethod
    def validate_filled_form_params(uri, data):
        if not data.get('entityUri'):
            raise exceptions.RequiredParameter('entityUri')
        if not data.get('entityType'):
            raise exceptions.RequiredParameter('entityType')

    @staticmethod
    def validate_enrich_fields_params(mf_fields, data):
        fields = data.get('fields')
        if not fields:
            raise exceptions.RequiredParameter('fields')
        for f in fields:
            if not f.get('fieldUri'):
                raise exceptions.RequiredParameter('fieldUri')
            mf_field = next((field for field in mf_fields if field.uri == f.get('fieldUri')), None)
            if not mf_field:
                raise exceptions.ObjectNotFound('MetadataFormField', f.get('fieldUri'))
            if not f.get('value') and mf_field.required:
                raise exceptions.RequiredParameter('value')
            f['field'] = mf_field


class AttachedMetadataFormService:
    @staticmethod
    def create_attached_metadata_form(uri, data):
        AttachedMetadataFormValidationService.validate_filled_form_params(uri, data)
        with get_context().db_engine.scoped_session() as session:
            mf = MetadataFormRepository.get_metadata_form(session, uri)
            if not mf:
                raise exceptions.ObjectNotFound('MetadataForm', uri)
            mf_fields = MetadataFormRepository.get_metadata_form_fields(session, uri)
            AttachedMetadataFormValidationService.validate_enrich_fields_params(mf_fields, data)

            amf = MetadataFormRepository.create_attached_metadata_form(session, uri, data)
            for f in data.get('fields'):
                MetadataFormRepository.create_attached_metadata_form_field(
                    session, amf.uri, f.get('field'), f.get('value')
                )
            return amf

    @staticmethod
    def get_attached_metadata_form(uri):
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.get_attached_metadata_form(session, uri)

    @staticmethod
    def get_attached_metadata_form_fields(uri):
        with get_context().db_engine.scoped_session() as session:
            return MetadataFormRepository.get_all_attached_metadata_form_fields(session, uri)

    @staticmethod
    def list_attached_forms(filter=None):
        context = get_context()
        groups = context.groups
        username = context.username
        is_da_admin = TenantPolicyValidationService.is_tenant_admin(groups)
        filter = filter if filter is not None else {}
        user_orgs, user_envs = None, None
        if not is_da_admin:
            with get_context().db_engine.scoped_session() as session:
                user_envs = EnvironmentRepository.query_user_environments(session, username, groups, {})
                user_envs = [e.environmentUri for e in user_envs]
                user_orgs = OrganizationRepository.query_user_organizations(session, username, groups, {})
                user_orgs = [o.organizationUri for o in user_orgs]
        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=MetadataFormRepository.query_attached_metadata_forms(
                    session, is_da_admin, groups, user_envs, user_orgs, filter
                ),
                page=filter.get('page', 1),
                page_size=filter.get('pageSize', 10),
            ).to_dict()

    @staticmethod
    def delete_attached_metadata_form(uri):
        mf = AttachedMetadataFormService.get_attached_metadata_form(uri)
        with get_context().db_engine.scoped_session() as session:
            return session.delete(mf)
