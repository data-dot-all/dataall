from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository

class MetadataFormFilledValidationService:
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



class MetadataFormFilledService:
    @staticmethod
    def create_filled_metadata_form(uri, data):
        with get_context().db_engine.scoped_session() as session:
            mf = MetadataFormRepository.get_metadata_form(session, uri)
            if not mf:
                raise exceptions.ObjectNotFound('MetadataForm', uri)
            mf_fields = MetadataFormRepository.get_metadata_form_fields(session, uri)
