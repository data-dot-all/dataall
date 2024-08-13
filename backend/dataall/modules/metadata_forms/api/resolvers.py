from dataall.base.api.context import Context
from dataall.modules.catalog.services.glossaries_service import GlossariesService
from dataall.modules.metadata_forms.db.metadata_form_models import MetadataForm, MetadataFormField
from dataall.modules.metadata_forms.services.metadata_form_service import MetadataFormService


def create_metadata_form(context: Context, source, input):
    return MetadataFormService.create_metadata_form(input)


def delete_metadata_form(context: Context, source, formUri):
    return MetadataFormService.delete_metadata_form_by_uri(formUri)


def list_metadata_forms(context: Context, source, filter=None):
    return MetadataFormService.paginated_metadata_form_list(filter)


def get_home_entity_name(context: Context, source: MetadataForm):
    return MetadataFormService.get_home_entity_name(source)


def get_metadata_form(context: Context, source, uri):
    return MetadataFormService.get_metadata_form_by_uri(uri)


def get_form_fields(context: Context, source: MetadataForm):
    return MetadataFormService.get_metadata_form_fields(source.uri)


def create_metadata_form_fields(context: Context, source, formUri, input):
    return MetadataFormService.create_metadata_form_fields(formUri, input)


def delete_metadata_form_field(context: Context, source, formUri, fieldUri):
    return MetadataFormService.delete_metadata_form_field(formUri, fieldUri)


def batch_metadata_form_field_update(context: Context, source, formUri, input):
    return MetadataFormService.batch_metadata_form_field_update(formUri, input)


def get_fields_glossary_node_name(context: Context, source: MetadataFormField):
    return GlossariesService.get_node(source.glossaryNodeUri).label if source.glossaryNodeUri else None
