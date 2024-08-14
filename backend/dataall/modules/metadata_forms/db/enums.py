from dataall.base.api.constants import GraphQLEnumMapper


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
    Datasets = 'Dataset'
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


class MetadataFormEnforcementSeverity(GraphQLEnumMapper):
    Mandatory = 'Mandatory'
    Recommended = 'Recommended'


class MetadataFormEnforcementScope(GraphQLEnumMapper):
    Item = 'Item Level'
    Dataset = 'Dataset Level'
    Environment = 'Environmental Level'
    Organization = 'Organizational Level'
    Global = 'Global'


class MetadataFormUserRoles(GraphQLEnumMapper):
    Owner = 'Owner'
    User = 'User'
