import { gql } from 'apollo-boost';

export const deleteDashboard = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  mutation: gql`
    mutation deleteDashboard($dashboardUri: String!) {
      deleteDashboard(dashboardUri: $dashboardUri)
    }
  `
});
