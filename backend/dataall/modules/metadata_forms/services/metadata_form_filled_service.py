from dataall.base.context import get_context
from dataall.base.db import exceptions, paginate
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository


class AttachedMetadataFormValidationService:
    @staticmethod
    def validate_filled_form_params(uri, data):
        if not data.get('entityUri'):
            raise exceptions.RequiredParameter('entityUri')
        if not data.get('entityType'):
            raise exceptions.RequiredParameter('entityType')

    @staticmethod
    def validate_fields_params(mf_fields, data):
        fields = data.get('fields')
        if not fields:
            raise exceptions.RequiredParameter('fields')


class AttachedMetadataFormService:
    @staticmethod
    def create_attached_metadata_form(uri, data):
        AttachedMetadataFormValidationService.validate_filled_form_params(uri, data)
        with get_context().db_engine.scoped_session() as session:
            mf = MetadataFormRepository.get_metadata_form(session, uri)
            if not mf:
                raise exceptions.ObjectNotFound('MetadataForm', uri)
            mf_fields = MetadataFormRepository.get_metadata_form_fields(session, uri)
            AttachedMetadataFormValidationService.validate_fields_params(mf_fields, data)

            amf = MetadataFormRepository.create_attached_metadata_form(session, uri, data)
            for f in data.get('fields'):
                base_field = next((field for field in mf_fields if field.uri == f.get('uri')), None)
                MetadataFormRepository.create_attached_metadata_form_field(session, amf.uri, base_field, f.get('value'))
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
        if not filter:
            filter = {}

        with get_context().db_engine.scoped_session() as session:
            return paginate(
                query=MetadataFormRepository.query_attached_metadata_forms(session, filter),
                page=filter.get('page', 1),
                page_size=filter.get('pageSize', 10),
            ).to_dict()
