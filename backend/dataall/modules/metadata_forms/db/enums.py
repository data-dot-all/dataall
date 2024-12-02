from dataall.base.api.constants import GraphQLEnumMapper
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup, ConsumptionRole
from dataall.core.organizations.db.organization_models import Organization, OrganizationGroup
from dataall.modules.dashboards.db.dashboard_models import Dashboard
from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioDomain
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset, DatasetTable, DatasetStorageLocation, DatasetBucket
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.worksheets.db.worksheet_models import Worksheet


class MetadataFormVisibility(GraphQLEnumMapper):
    Team = 'Team Only'
    Environment = 'Environment-Wide'
    Organization = 'Organization-Wide'
    Global = 'Global'


class MetadataFormFieldType(GraphQLEnumMapper):
    String = 'String'
    Integer = 'Integer'
    Boolean = 'Boolean'
    GlossaryTerm = 'Glossary Term'


class MetadataFormEntityTypes(GraphQLEnumMapper):
    Organizations = 'Organization'
    OrganizationTeams = 'Organization Team'
    Environments = 'Environment'
    EnvironmentTeams = 'Environment Team'
    S3Datasets = 'S3-Dataset'
    RDDatasets = 'Redshift-Dataset'
    Worksheets = 'Worksheets'
    Dashboards = 'Dashboard'
    ConsumptionRoles = 'Consumption Role'
    Notebooks = 'Notebook'
    MLStudioEntities = 'ML Studio Entity'
    Pipelines = 'Pipeline'
    Tables = 'Table'
    Folder = 'Folder'
    Bucket = 'Bucket'
    Share = 'Share'
    ShareItem = 'Share Item'

    @staticmethod
    def get_entity_class(value: str):
        classes = {
            MetadataFormEntityTypes.Organizations.value: (
                Organization,
                MetadataFormEnforcementScope.Global,
                lambda o: (o.organizationUri, o.SamlGroupName, o.lable),
            ),
            MetadataFormEntityTypes.OrganizationTeams.value: (
                OrganizationGroup,
                MetadataFormEnforcementScope.Organization,
                lambda o: (o.organizationUri + o.groupUri, o.invitedBy, o.groupUri),
            ),
            MetadataFormEntityTypes.Environments.value: (
                Environment,
                MetadataFormEnforcementScope.Organization,
                lambda o: (o.environmentUri, o.SamlGroupName, o.lable),
            ),
            MetadataFormEntityTypes.EnvironmentTeams.value: (
                EnvironmentGroup,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.environmentUri + o.groupUri, o.invitedBy, o.groupUri),
            ),
            MetadataFormEntityTypes.S3Datasets.value: (
                S3Dataset,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.datasetUri, o.SamlAdminGroupName, o.groupUri),
            ),
            MetadataFormEntityTypes.RDDatasets.value: (
                RedshiftDataset,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.datasetUri, o.SamlAdminGroupName, o.groupUri),
            ),
            MetadataFormEntityTypes.Worksheets.value: (
                Worksheet,
                MetadataFormEnforcementScope.Global,
                lambda o: (o.worksheetUri, o.SamlAdminGroupName, o.lable),
            ),
            MetadataFormEntityTypes.Dashboards.value: (
                Dashboard,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.dashboardUri, o.SamlGroupName, o.groupUri),
            ),
            MetadataFormEntityTypes.ConsumptionRoles.value: (
                ConsumptionRole,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.consumptionRoleUri, o.groupUri, o.consumptionRoleName),
            ),
            MetadataFormEntityTypes.Notebooks.value: (
                SagemakerNotebook,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.notebookUri, o.SamlAdminGroupName, o.lable),
            ),
            MetadataFormEntityTypes.MLStudioEntities.value: (
                SagemakerStudioDomain,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.sagemakerStudioUri, o.SamlGroupName, o.lable),
            ),
            MetadataFormEntityTypes.Pipelines.value: (
                DataPipeline,
                MetadataFormEnforcementScope.Environment,
                lambda o: (o.DataPipelineUri, o.SamlGroupName, o.lable),
            ),
            MetadataFormEntityTypes.Tables.value: (
                DatasetTable,
                MetadataFormEnforcementScope.Dataset,
                lambda o: (o.tableUri, None, o.GlueTableName),  # ToDo: resolve owner
            ),
            MetadataFormEntityTypes.Folder.value: (
                DatasetStorageLocation,
                MetadataFormEnforcementScope.Dataset,
                lambda o: (o.locationUri, None, o.S3BucketName),  # ToDo: resolve owner
            ),
            MetadataFormEntityTypes.Bucket.value: (
                DatasetBucket,
                MetadataFormEnforcementScope.Dataset,
                lambda o: (o.bucketUri, None, o.S3BucketName),  # ToDo: resolve owner
            ),
            MetadataFormEntityTypes.Share.value: (
                ShareObject,
                MetadataFormEnforcementScope.Dataset,
                lambda o: (o.shareUri, o.groupUri, o.shareUri),
            ),
        }


class MetadataFormEnforcementSeverity(GraphQLEnumMapper):
    Mandatory = 'Mandatory'
    Recommended = 'Recommended'


class MetadataFormEnforcementScope(GraphQLEnumMapper):
    Dataset = 'Dataset Level'
    Environment = 'Environmental Level'
    Organization = 'Organizational Level'
    Global = 'Global'


class MetadataFormUserRoles(GraphQLEnumMapper):
    Owner = 'Owner'
    User = 'User'
