import { gql } from 'apollo-boost';

export const updateShareRejectReason = ({ shareUri, rejectPurpose }) => ({
  variables: {
    shareUri,
    rejectPurpose
  },
  mutation: gql`
    mutation updateShareRejectReason(
      $shareUri: String!
      $rejectPurpose: String!
    ) {
      updateShareRejectReason(
        shareUri: $shareUri
        rejectPurpose: $rejectPurpose
      )
    }
  `
});
