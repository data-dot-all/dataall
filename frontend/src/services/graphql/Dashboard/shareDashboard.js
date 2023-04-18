import { gql } from 'apollo-boost';

export const shareDashboard = (dashboardUri, principalId) => ({
  variables: {
    dashboardUri,
    principalId
  },
  mutation: gql`
    mutation shareDashboard($dashboardUri: String!, $principalId: String!) {
      shareDashboard(dashboardUri: $dashboardUri, principalId: $principalId) {
        shareUri
        status
      }
    }
  `
});
