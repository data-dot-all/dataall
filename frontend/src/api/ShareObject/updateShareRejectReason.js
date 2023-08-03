import { gql } from 'apollo-boost';

const updateShareRejectReason = ({ shareUri, rejectPurpose }) => ({
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

export default updateShareRejectReason;
