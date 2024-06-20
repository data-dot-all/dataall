import { gql } from 'apollo-boost';

export const updateDashboard = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation updateDashboard($input: UpdateDashboardInput!) {
      updateDashboard(input: $input) {
        dashboardUri
        name
        label
        created
      }
    }
  `
});
