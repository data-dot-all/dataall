from dataclasses import field, dataclass

from dataall.base.api import gql
from dataall.base.api.graphql_api import api_input, api_object, Page, PageFilter
from dataall.core.environment.db.models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.modules.dashboards import Dashboard
from dataall.modules.dashboards.api.enums import DashboardRole


@api_object("Dashboard")
@dataclass
class DashboardDto(gql.ObjectType):
    dashboardUri: gql.ID
    name: str
    label: str
    description: str
    DashboardId: str
    tags: [str]
    created: str
    updated: str
    owner: str
    SamlGroupName: str
    organization: gql.Ref('Organization') = None
    environment: gql.Ref('Environment') = None
    userRoleForDashboard: DashboardRole = None
    terms: [str] = field(default_factory=list)
    upvotes: int = 0

    def __init__(
        self,
        dashboard: Dashboard,
        organization: Organization,
        role: DashboardRole,
        environment: Environment,
        terms,
        upvotes: int
    ):
        for attr in Dashboard.__dict__:
            if not attr.startswith('_'):
                setattr(self, attr, getattr(dashboard, attr))

        self.environment = environment
        self.organization = organization
        self.role = role
        self.upvotes = upvotes
        self.terms = terms
        self.userRoleForDashboard = role


@api_input("ImportDashboardInput")
@dataclass
class ImportDashboardInput(gql.InputType):
    label: str
    environmentUri: str
    dashboardId: str
    SamlGroupName: str
    description = "No description provided"
    tags: [str] = field(default_factory=list)
    terms: [str] = field(default_factory=list)


@api_input('UpdateDashboardInput')
@dataclass
class UpdateDashboardInput(gql.InputType):
    dashboardUri: str
    label: str
    description: str = "No description provided"
    tags: [str] = field(default_factory=list)
    terms: [str] = field(default_factory=list)


@api_input('DashboardFilter')
@dataclass
class DashboardFilter(PageFilter):
    pass


@api_object(name="DashboardSearchResults")
@dataclass
class DashboardSearchResults(Page):
    nodes: [DashboardDto]


@api_object("DashboardShare")
@dataclass
class DashboardShareDto(gql.ObjectType):
    shareUri: str
    dashboardUri: str
    name: str
    label: str
    SamlGroupName: str
    status: str
    owner: str
    tags: str
    created: str
    updated: str


@api_object(name="DashboardShareSearchResults")
@dataclass
class DashboardShareSearchResults(Page):
    nodes: [DashboardShareDto]


@api_input(name="DashboardShareFilter")
@dataclass
class DashboardShareFilter(PageFilter):
    pass
