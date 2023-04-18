import { gql } from 'apollo-boost';

export const deleteDashboard = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  mutation: gql`
    mutation importDashboard($dashboardUri: String!) {
      deleteDashboard(dashboardUri: $dashboardUri)
    }
  `
});
