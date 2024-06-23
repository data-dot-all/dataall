import { gql } from 'apollo-boost';

export const importDashboard = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation importDashboard($input: ImportDashboardInput!) {
      importDashboard(input: $input) {
        dashboardUri
        name
        label
        DashboardId
        created
      }
    }
  `
});
