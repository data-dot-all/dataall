import { gql } from 'apollo-boost';

export const getDashboard = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  query: gql`
    query GetDashboard($dashboardUri: String!) {
      getDashboard(dashboardUri: $dashboardUri) {
        dashboardUri
        name
        owner
        SamlGroupName
        description
        label
        created
        tags
        userRoleForDashboard
        DashboardId
        upvotes
        restricted {
          region
          AwsAccountId
        }
        environment {
          environmentUri
          label
          organization {
            organizationUri
            label
          }
        }
        terms {
          count
          nodes {
            nodeUri
            path
            label
          }
        }
      }
    }
  `
});
