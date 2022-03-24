import { gql } from 'apollo-boost';

const updateDashboard = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation updateDashboard(
            $input:UpdateDashboardInput,
        ){
            updateDashboard(input:$input){
                dashboardUri
                name
                label
                created
            }
        }`
});

export default updateDashboard;
