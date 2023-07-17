import { gql } from 'apollo-boost';

const approveDashboardShare = (shareUri) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation approveDashboardShare($shareUri: String!) {
      approveDashboardShare(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});

export default approveDashboardShare;
