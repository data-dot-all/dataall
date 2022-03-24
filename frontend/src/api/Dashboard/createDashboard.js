import { gql } from 'apollo-boost';

const createDashboard = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`mutation CreateDashboard(
            $input:NewDashboardInput,
        ){
            createDashboard(input:$input){
                dashboardUri
                name
                label
                created
            }
        }`
});

export default createDashboard;
