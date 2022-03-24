import { gql } from 'apollo-boost';

const rejectDashboardShare = (shareUri) => ({
  variables: {
    shareUri
  },
  mutation: gql`mutation rejectDashboardShare($shareUri:String!){
            rejectDashboardShare(shareUri:$shareUri){
                shareUri
                status
            }
        }`
});

export default rejectDashboardShare;
