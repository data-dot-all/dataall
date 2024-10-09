from dataall.base.api.context import Context
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.catalog.services.glossaries_service import GlossariesService
from dataall.modules.metadata_forms.db.metadata_form_models import (
    MetadataForm,
    MetadataFormField,
    AttachedMetadataForm,
    AttachedMetadataFormField,
)
from dataall.modules.metadata_forms.services.attached_metadata_form_service import AttachedMetadataFormService
from dataall.modules.metadata_forms.services.metadata_form_permissions import MANAGE_METADATA_FORMS
from dataall.modules.metadata_forms.services.metadata_form_service import MetadataFormService, MetadataFormAccessService


def create_metadata_form(context: Context, source, input):
    return MetadataFormService.create_metadata_form(data=input)


def create_attached_metadata_form(context: Context, source, formUri, input):
    return AttachedMetadataFormService.create_attached_metadata_form(uri=formUri, data=input)


def delete_metadata_form(context: Context, source, formUri):
    return MetadataFormService.delete_metadata_form_by_uri(uri=formUri)


def delete_attached_metadata_form(context: Context, source, attachedFormUri):
    return AttachedMetadataFormService.delete_attached_metadata_form(uri=attachedFormUri)


def list_user_metadata_forms(context: Context, source, filter=None):
    return MetadataFormService.paginated_user_metadata_form_list(filter=filter)


def list_entity_metadata_forms(context: Context, source, filter=None):
    return MetadataFormService.paginated_entity_metadata_form_list(filter=filter)


def get_home_entity_name(context: Context, source: MetadataForm):
    return MetadataFormService.get_home_entity_name(metadata_form=source)


def get_metadata_form(context: Context, source, uri):
    return MetadataFormService.get_metadata_form_by_uri(uri=uri)


def resolve_metadata_form(context: Context, source: AttachedMetadataForm):
    return MetadataFormService.get_metadata_form_by_uri(source.metadataFormUri)


def get_form_fields(context: Context, source: MetadataForm):
    return MetadataFormService.get_metadata_form_fields(uri=source.uri)


def create_metadata_form_fields(context: Context, source, formUri, input):
    return MetadataFormService.create_metadata_form_fields(uri=formUri, data_arr=input)


def delete_metadata_form_field(context: Context, source, formUri, fieldUri):
    return MetadataFormService.delete_metadata_form_field(uri=formUri, fieldUri=fieldUri)


def batch_metadata_form_field_update(context: Context, source, formUri, input):
    return MetadataFormService.batch_metadata_form_field_update(uri=formUri, data=input)


def get_user_role(context: Context, source: MetadataForm):
    return MetadataFormAccessService.get_user_role(uri=source.uri)


def get_fields_glossary_node_name(context: Context, source: MetadataFormField):
    return GlossariesService.get_node(source.glossaryNodeUri).label if source.glossaryNodeUri else None


def list_attached_forms(context: Context, source, filter=None):
    return AttachedMetadataFormService.list_attached_forms(filter=filter)


def get_attached_form_fields(context: Context, source: AttachedMetadataForm):
    return AttachedMetadataFormService.get_attached_metadata_form_fields(uri=source.uri)


def get_attached_metadata_form(context: Context, source, uri):
    return AttachedMetadataFormService.get_attached_metadata_form(uri=uri)


def has_tenant_permissions_for_metadata_forms(context: Context, source: MetadataForm):
    return TenantPolicyService.has_user_tenant_permission(
        groups=context.groups,
        tenant_name=TenantPolicyService.TENANT_NAME,
        permission_name=MANAGE_METADATA_FORMS,
    )


def resolve_metadata_form_field(context: Context, source: AttachedMetadataFormField):
    return MetadataFormService.get_metadata_form_field_by_uri(uri=source.fieldUri)


def get_entity_metadata_form_permissions(context: Context, source, entityUri):
    return MetadataFormService.get_mf_permissions(entityUri=entityUri)
