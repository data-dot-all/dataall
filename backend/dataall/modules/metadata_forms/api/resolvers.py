from dataall.base.api.context import Context
from dataall.modules.metadata_forms.db.metadata_form_models import MetadataForm
from dataall.modules.metadata_forms.services.metadata_form_service import MetadataFormService, MetadataFormAccessService


def create_metadata_form(context: Context, source, input):
    return MetadataFormService.create_metadata_form(data=input)


def delete_metadata_form(context: Context, source, formUri):
    return MetadataFormService.delete_metadata_form_by_uri(uri=formUri)


def list_metadata_forms(context: Context, source, filter=None):
    return MetadataFormService.paginated_metadata_form_list(filter=filter)


def get_home_entity_name(context: Context, source: MetadataForm):
    return MetadataFormService.get_home_entity_name(metadata_form=source)


def get_metadata_form(context: Context, source, uri):
    return MetadataFormService.get_metadata_form_by_uri(uri=uri)


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
