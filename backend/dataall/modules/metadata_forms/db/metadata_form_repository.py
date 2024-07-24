from dataall.modules.metadata_forms.db.metadata_form_models import MetadataForm
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
        # toDo: implement filter
        query = session.query(MetadataForm)
        return query.all()
