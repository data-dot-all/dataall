import { gql } from 'apollo-boost';

export const searchDashboards = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query searchDashboards($filter: DashboardFilter) {
      searchDashboards(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          dashboardUri
          name
          owner
          SamlGroupName
          description
          label
          created
          tags
          userRoleForDashboard
          upvotes
          organization {
            organizationUri
            label
            name
          }
          environment {
            environmentUri
            name
            label
            AwsAccountId
            region
          }
        }
      }
    }
  `
});
