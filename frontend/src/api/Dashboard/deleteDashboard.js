import { gql } from 'apollo-boost';

const deleteDashboard = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  mutation: gql`
    mutation deleteDashboard($dashboardUri: String!) {
      deleteDashboard(dashboardUri: $dashboardUri)
    }
  `
});

export default deleteDashboard;
