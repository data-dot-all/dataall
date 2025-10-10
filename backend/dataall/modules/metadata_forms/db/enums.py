from dataall.base.api.constants import GraphQLEnumMapper
from dataall.core.metadata_manager.metadata_form_entity_manager import MetadataFormEntityTypes


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


class MetadataFormEnforcementSeverity(GraphQLEnumMapper):
    Mandatory = 'Mandatory'
    Recommended = 'Recommended'


class MetadataFormEnforcementScope(GraphQLEnumMapper):
    Dataset = 'Dataset Level'
    Environment = 'Environmental Level'
    Organization = 'Organizational Level'
    Global = 'Global'

    @classmethod
    def _ordering(cls):
        return ['Global', 'Organization', 'Environment', 'Dataset']

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.__class__._ordering().index(self._name_) > self.__class__._ordering().index(other._name_)
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.__class__._ordering().index(self._name_) < self.__class__._ordering().index(other._name_)
        return NotImplemented


class MetadataFormUserRoles(GraphQLEnumMapper):
    Owner = 'Owner'
    User = 'User'


ENTITY_SCOPE_BY_TYPE = {
    MetadataFormEntityTypes.Organization.value: MetadataFormEnforcementScope.Global,
    MetadataFormEntityTypes.OrganizationTeam.value: MetadataFormEnforcementScope.Organization,
    MetadataFormEntityTypes.Environment.value: MetadataFormEnforcementScope.Organization,
    MetadataFormEntityTypes.EnvironmentTeam.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.S3Dataset.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.RDDataset.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.Worksheet.value: MetadataFormEnforcementScope.Global,
    MetadataFormEntityTypes.Dashboard.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.ConsumptionRole.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.Notebook.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.MLStudioUser.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.Pipeline.value: MetadataFormEnforcementScope.Environment,
    MetadataFormEntityTypes.Table.value: MetadataFormEnforcementScope.Dataset,
    MetadataFormEntityTypes.Folder.value: MetadataFormEnforcementScope.Dataset,
    MetadataFormEntityTypes.Bucket.value: MetadataFormEnforcementScope.Dataset,
    MetadataFormEntityTypes.Share.value: MetadataFormEnforcementScope.Dataset,
}
