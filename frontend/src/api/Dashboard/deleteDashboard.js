import { gql } from 'apollo-boost';

const deleteDashboard = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  mutation: gql`mutation importDashboard(
            $dashboardUri:String!,
        ){
            deleteDashboard(dashboardUri:$dashboardUri)
        }`
});

export default deleteDashboard;
