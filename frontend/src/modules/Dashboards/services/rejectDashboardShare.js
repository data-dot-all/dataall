import { gql } from 'apollo-boost';

export const rejectDashboardShare = (shareUri) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation rejectDashboardShare($shareUri: String!) {
      rejectDashboardShare(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});
