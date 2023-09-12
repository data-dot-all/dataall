import { gql } from 'apollo-boost';

export const listDashboardShares = ({ dashboardUri, filter }) => ({
  variables: {
    dashboardUri,
    filter
  },
  query: gql`
    query listDashboardShares(
      $dashboardUri: String!
      $filter: DashboardShareFilter!
    ) {
      listDashboardShares(dashboardUri: $dashboardUri, filter: $filter) {
        count
        nodes {
          dashboardUri
          shareUri
          SamlGroupName
          owner
          created
          status
        }
      }
    }
  `
});
