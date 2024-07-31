from sqlalchemy import or_

from dataall.modules.metadata_forms.db.metadata_form_models import MetadataForm, MetadataFormField
from dataall.modules.metadata_forms.db.enums import MetadataFormVisibility


class MetadataFormRepository:
    @staticmethod
    def create_metadata_form(session, data=None):
        mf: MetadataForm = MetadataForm(
            name=data.get('name'),
            description=data.get('description'),
            SamlGroupName=data.get('SamlGroupName'),
            visibility=data.get('visibility'),
            homeEntity=data.get('homeEntity'),
        )
        session.add(mf)
        session.commit()
        return mf

    @staticmethod
    def get_metadata_form(session, uri):
        return session.query(MetadataForm).get(uri)

    @staticmethod
    def list_metadata_forms(session, filter=None):
        query = session.query(MetadataForm)
        if filter and filter.get('search_input'):
            query = query.filter(
                or_(
                    MetadataForm.name.ilike('%' + filter.get('search_input') + '%'),
                    MetadataForm.description.ilike('%' + filter.get('search_input') + '%'),
                )
            )
        return query

    @staticmethod
    def get_metadata_form_fields(session, form_uri):
        return session.query(MetadataFormField).filter(MetadataFormField.metadataFormUri == form_uri).all()

    @staticmethod
    def create_metadata_form_field(session, uri, data):
        field: MetadataFormField = MetadataFormField(
            metadataFormUri=uri,
            name=data.get('name'),
            type=data.get('type'),
            required=data.get('required', False),
            glossaryNodeUri=data.get('glossaryNodeUri', None),
            possibleValues=data.get('possibleValues', None),
        )
        session.add(field)
        session.commit()
        return field
