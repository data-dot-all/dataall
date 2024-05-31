import logging

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.base.db import paginate
from dataall.base.db.exceptions import ObjectNotFound
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification, Language
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset

logger = logging.getLogger(__name__)


class RedshiftDatasetRepository(EnvironmentResource):
    """DAO layer for Redshift Datasets"""

    @classmethod
    def create_redshift_dataset(cls, session, username, env: Environment, data: dict):
        organization = OrganizationRepository.get_organization_by_uri(session, env.organizationUri)
        dataset = RedshiftDataset(
            label=data.get('label'),
            owner=username,
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            AwsAccountId=env.AwsAccountId,
            SamlAdminGroupName=data['SamlAdminGroupName'],
            region=env.region,
            environmentUri=env.environmentUri,
            organizationUri=env.organizationUri,
            language=data.get('language', Language.English.value),
            confidentiality=data.get('confidentiality', ConfidentialityClassification.Unclassified.value),
            topics=data.get('topics', []),
            businessOwnerEmail=data.get('businessOwnerEmail'),
            businessOwnerDelegationEmails=data.get('businessOwnerDelegationEmails', []),
            stewards=data.get('stewards') if data.get('stewards') else data['SamlAdminGroupName'],
            autoApprovalEnabled=data.get('autoApprovalEnabled', False),
            connectionUri=data.get('connectionUri'),
            importPattern=data.get('importPattern'),
        )
        session.add(dataset)
        session.commit()

        activity = Activity(
            action='redshift-dataset:import',
            label='redshift-dataset:import',
            owner=dataset.owner,
            summary=f'{dataset.owner} imported redshift dataset {dataset.name} in {env.name} on organization {organization.name}',
            targetUri=dataset.datasetUri,
            targetType='redshift-dataset',
        )
        session.add(activity)
        return dataset
