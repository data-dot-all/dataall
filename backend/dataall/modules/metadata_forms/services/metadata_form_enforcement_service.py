from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository, DatasetListRepository
from dataall.modules.metadata_forms.db.enums import (
    MetadataFormEnforcementScope,
    MetadataFormEntityTypes,
    MetadataFormEnforcementSeverity,
)
from dataall.modules.metadata_forms.db.metadata_form_repository import MetadataFormRepository
from dataall.modules.metadata_forms.services.metadata_form_access_service import MetadataFormAccessService
from dataall.modules.metadata_forms.services.metadata_form_permissions import (
    MANAGE_METADATA_FORMS,
    ENFORCE_METADATA_FORM,
)
from dataall.modules.notifications.db.notification_repositories import NotificationRepository


class MetadataFormEnforcementRequestValidationService:
    @staticmethod
    def validate_create_request(data):
        if 'metadataFormUri' not in data:
            raise exceptions.RequiredParameter('metadataFormUri')

        if 'level' not in data:
            raise exceptions.RequiredParameter('level')

        if 'severity' not in data:
            raise exceptions.RequiredParameter('severity')

        if data.get('level') != MetadataFormEnforcementScope.Global.value:
            if 'homeEntity' not in data:
                raise exceptions.RequiredParameter('homeEntity')

        if 'entityTypes' not in data:
            raise exceptions.RequiredParameter('entityTypes')

        # check that values are valid for the enums
        MetadataFormEnforcementScope(data.get('level'))
        MetadataFormEnforcementSeverity(data.get('severity'))


class MetadataFormEnforcementService:
    @staticmethod
    def _get_entity_uri(session, data):
        return data.get('homeEntity')

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_METADATA_FORMS)
    @MetadataFormAccessService.can_perform(ENFORCE_METADATA_FORM)
    def create_mf_enforcement_rule(uri, data):
        MetadataFormEnforcementRequestValidationService.validate_create_request(data)
        MetadataFormAccessService.check_enforcement_access(data.get('homeEntity'), data.get('level'))
        with get_context().db_engine.scoped_session() as session:
            mf = MetadataFormRepository.get_metadata_form(session, uri)
            version = data.get('version') or MetadataFormRepository.get_metadata_form_version_number_latest(
                session, uri
            )
            rule = MetadataFormRepository.create_mf_enforcement_rule(session, uri, data, version)

            affected_entities = MetadataFormEnforcementService.get_affected_entities(rule.uri, rule=rule)
            for entity in affected_entities:
                if entity['owner']:
                    NotificationRepository.create_notification(
                        session,
                        recipient=entity['owner'],
                        target_uri=f'{entity["uri"]}|{entity["type"]}',
                        message=f'Usage of metadata form "{mf.name}" was enforced for {entity["uri"]} {entity["type"]}',
                        notification_type='METADATA_FORM_ENFORCED',
                    )

        return rule

    @staticmethod
    def get_affected_organizations(uri, rule=None):
        with get_context().db_engine.scoped_session() as session:
            if not rule:
                rule = MetadataFormRepository.get_mf_enforcement_rule_by_uri(session, uri)
            if rule.level == MetadataFormEnforcementScope.Global.value:
                return OrganizationRepository.query_all_active_organizations(session).all()
            if rule.level == MetadataFormEnforcementScope.Organization.value:
                return [OrganizationRepository.get_organization_by_uri(session, rule.homeEntity)]
            return []

    @staticmethod
    def get_affected_environments(uri, rule=None):
        with get_context().db_engine.scoped_session() as session:
            if not rule:
                rule = MetadataFormRepository.get_mf_enforcement_rule_by_uri(session, uri)
            if rule.level == MetadataFormEnforcementScope.Global.value:
                return EnvironmentRepository.query_all_active_environments(session)
            if rule.level == MetadataFormEnforcementScope.Organization.value:
                return EnvironmentRepository.get_all_envs_by_organization(session, rule.homeEntity)
            if rule.level == MetadataFormEnforcementScope.Environment.value:
                return [EnvironmentRepository.get_environment_by_uri(session, rule.homeEntity)]
            return []

    @staticmethod
    def get_affected_datasets(uri, rule=None):
        with get_context().db_engine.scoped_session() as session:
            if not rule:
                rule = MetadataFormRepository.get_mf_enforcement_rule_by_uri(session, uri)
            if rule.level == MetadataFormEnforcementScope.Global.value:
                return DatasetListRepository.query_datasets(session).all()
            if rule.level == MetadataFormEnforcementScope.Organization.value:
                return DatasetListRepository.query_datasets(session, organizationUri=rule.homeEntity).all()
            if rule.level == MetadataFormEnforcementScope.Environment.value:
                return DatasetListRepository.query_datasets(session, environmentUri=rule.homeEntity).all()
            if rule.level == MetadataFormEnforcementScope.Dataset.value:
                return [DatasetBaseRepository.get_dataset_by_uri(session, rule.homeEntity)]
            return []

    @staticmethod
    def form_affected_entity_object(uri, owner, type, rule):
        with get_context().db_engine.scoped_session() as session:
            attached = MetadataFormRepository.query_all_attached_metadata_forms_for_entity(
                session,
                entityUri=uri,
                metadataFormUri=rule.metadataFormUri,
                version=rule.version,
            )
        return {'type': type, 'uri': uri, 'owner': owner, 'attached': attached.first()}

    @staticmethod
    def get_affected_entities(uri, rule=None):
        affected_entities = []
        with get_context().db_engine.scoped_session() as session:
            if not rule:
                rule = MetadataFormRepository.get_mf_enforcement_rule_by_uri(session, uri)

            orgs = MetadataFormEnforcementService.get_affected_organizations(uri, rule)
            affected_entities.extend(
                [
                    MetadataFormEnforcementService.form_affected_entity_object(
                        o.organizationUri, o.SamlGroupName, MetadataFormEntityTypes.Organizations.value, rule
                    )
                    for o in orgs
                ]
            )

            envs = MetadataFormEnforcementService.get_affected_environments(uri, rule)
            affected_entities.extend(
                [
                    MetadataFormEnforcementService.form_affected_entity_object(
                        e.environmentUri, e.SamlGroupName, MetadataFormEntityTypes.Environments.value, rule
                    )
                    for e in envs
                ]
            )

            datasets = MetadataFormEnforcementService.get_affected_datasets(uri, rule)
            affected_entities.extend(
                [
                    MetadataFormEnforcementService.form_affected_entity_object(
                        ds.datasetUri, ds.SamlAdminGroupName, ds.datasetType.value + '-Dataset', rule
                    )
                    for ds in datasets
                ]
            )

            entity_types = set(rule.entityTypes[:]) - {
                MetadataFormEntityTypes.Organizations.value,
                MetadataFormEntityTypes.Environments.value,
                MetadataFormEntityTypes.RDDatasets.value,
                MetadataFormEntityTypes.S3Datasets.value,
            }

            for entity_type in entity_types:
                entity_class, level, get_uri_and_owner = MetadataFormEntityTypes.get_entity_class(entity_type)
                all_entities = session.query(entity_class)
                if level == MetadataFormEnforcementScope.Organization.value:
                    all_entities = all_entities.filter(entity_class.organizationUri.in_([org.uri for org in orgs]))
                if level == MetadataFormEnforcementScope.Environment.value:
                    all_entities = all_entities.filter(entity_class.environmentUri.in_([env.uri for env in envs]))
                if level == MetadataFormEnforcementScope.Dataset.value:
                    all_entities = all_entities.filter(entity_class.datasetUri.in_([ds.uri for ds in datasets]))
                all_entities = all_entities.all()
                affected_entities.extend(
                    [
                        MetadataFormEnforcementService.form_affected_entity_object(
                            *get_uri_and_owner(e), entity_type, rule
                        )
                        for e in all_entities
                    ]
                )
            return affected_entities
