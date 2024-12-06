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
          restricted {
            region
            AwsAccountId
          }
          description
          label
          created
          tags
          userRoleForDashboard
          upvotes
          environment {
            environmentUri
            label
          }
        }
      }
    }
  `
});
