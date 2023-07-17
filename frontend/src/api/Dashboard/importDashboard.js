import { gql } from 'apollo-boost';

const importDashboard = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation importDashboard($input: ImportDashboardInput) {
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

export default importDashboard;
