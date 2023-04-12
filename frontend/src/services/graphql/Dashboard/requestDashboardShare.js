import { gql } from 'apollo-boost';

export const requestDashboardShare = (dashboardUri, principalId) => ({
  variables: {
    dashboardUri,
    principalId
  },
  mutation: gql`
    mutation requestDashboardShare(
      $dashboardUri: String!
      $principalId: String!
    ) {
      requestDashboardShare(
        dashboardUri: $dashboardUri
        principalId: $principalId
      ) {
        shareUri
        status
      }
    }
  `
});
