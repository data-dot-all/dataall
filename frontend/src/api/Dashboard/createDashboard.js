import { gql } from 'apollo-boost';

export const createDashboard = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateDashboard($input: NewDashboardInput) {
      createDashboard(input: $input) {
        dashboardUri
        name
        label
        created
      }
    }
  `
});
