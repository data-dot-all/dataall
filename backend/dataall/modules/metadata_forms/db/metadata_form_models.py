from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Boolean,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, validates

from dataall.base.db import Base, utils

from dataall.modules.metadata_forms.db.enums import MetadataFormFieldType


class MetadataForm(Base):
    __tablename__ = 'metadata_form'
    uri = Column(String, primary_key=True, default=utils.uuid('metadata_form'))
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
    visibility = Column(String, nullable=False)  # enum MetadataFormVisibility
    homeEntity = Column(String, nullable=True)


class MetadataFormEnforcementRule(Base):
    __tablename__ = 'metadata_form_enforcement_rule'
    uri = Column(String, primary_key=True, default=utils.uuid('rule'))
    metadataFormUri = Column(String, ForeignKey('metadata_form.uri'), nullable=False)
    level = Column(String, nullable=False)  # enum MetadataFormEnforcementScope
    entityTypes = Column(ARRAY(String), nullable=False)  # enum MetadataFormEntityTypes
    severity = Column(String, nullable=False)  # enum MetadataFormEnforcementSeverity


class MetadataFormField(Base):
    __tablename__ = 'metadata_form_field'
    metadataFormUri = Column(String, ForeignKey('metadata_form.uri'))
    uri = Column(String, primary_key=True, default=utils.uuid('field'))
    displayNumber = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # enum MetadataFormFieldType
    required = Column(Boolean, nullable=False)
    glossaryNodeUri = Column(String, ForeignKey('glossary_node.nodeUri'), nullable=True)
    possibleValues = Column(ARRAY(String), nullable=True)


class AttachedMetadataForm(Base):
    __tablename__ = 'attached_metadata_form'
    metadataFormUri = Column(String, ForeignKey('metadata_form.uri'), nullable=False)
    uri = Column(String, primary_key=True, default=utils.uuid('attached_form'))
    entityUri = Column(String, nullable=False)
    entityType = Column(String, nullable=False)


class AttachedMetadataFormField(Base):
    __tablename__ = 'attached_metadata_form_field'
    attachedFormUri = Column(String, ForeignKey('attached_metadata_form.uri'), primary_key=True)
    fieldUri = Column(String, ForeignKey('metadata_form_field.uri'), primary_key=True)
    type = Column(String, nullable=False)
    field = relationship('MetadataFormField', backref='attached_fields')

    __table_args__ = (PrimaryKeyConstraint('attachedFormUri', 'fieldUri'),)
    __mapper_args__ = {'polymorphic_identity': 'attached_metadata_form_field', 'polymorphic_on': type}

    @property
    def value(self):
        raise NotImplementedError('Basic AttachedMetadataFormField has no implemented property value')

    @validates('type')
    def update_type(self, key, new_type):
        if new_type != self.field.type:
            raise ValueError("Value type doesn't match field type")


class StringAttachedMetadataFormField(AttachedMetadataFormField):
    __tablename__ = 'string_attached_metadata_form_field'
    attachedFormUri = Column(String, primary_key=True)
    fieldUri = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    __mapper_args__ = {'polymorphic_identity': MetadataFormFieldType.String}

    __table_args__ = (
        ForeignKeyConstraint(
            ['attachedFormUri', 'fieldUri'],
            ['attached_metadata_form_field.attachedFormUri', 'attached_metadata_form_field.fieldUri'],
        ),
    )


class BooleanAttachedMetadataFormField(AttachedMetadataFormField):
    __tablename__ = 'boolean_attached_metadata_form_field'
    attachedFormUri = Column(String, primary_key=True)
    fieldUri = Column(String, primary_key=True)
    value = Column(Boolean, nullable=False)
    __mapper_args__ = {'polymorphic_identity': MetadataFormFieldType.Boolean}

    __table_args__ = (
        ForeignKeyConstraint(
            ['attachedFormUri', 'fieldUri'],
            ['attached_metadata_form_field.attachedFormUri', 'attached_metadata_form_field.fieldUri'],
        ),
    )


class IntegerAttachedMetadataFormField(AttachedMetadataFormField):
    __tablename__ = 'integer_attached_metadata_form_field'
    attachedFormUri = Column(String, primary_key=True)
    fieldUri = Column(String, primary_key=True)
    value = Column(Integer, nullable=False)
    __mapper_args__ = {'polymorphic_identity': MetadataFormFieldType.Integer}

    __table_args__ = (
        ForeignKeyConstraint(
            ['attachedFormUri', 'fieldUri'],
            ['attached_metadata_form_field.attachedFormUri', 'attached_metadata_form_field.fieldUri'],
        ),
    )


class GlossaryTermAttachedMetadataFormField(AttachedMetadataFormField):
    __tablename__ = 'glossary_term_attached_metadata_form_field'
    attachedFormUri = Column(String, primary_key=True)
    fieldUri = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    __mapper_args__ = {'polymorphic_identity': MetadataFormFieldType.GlossaryTerm}

    __table_args__ = (
        ForeignKeyConstraint(
            ['attachedFormUri', 'fieldUri'],
            ['attached_metadata_form_field.attachedFormUri', 'attached_metadata_form_field.fieldUri'],
        ),
    )
