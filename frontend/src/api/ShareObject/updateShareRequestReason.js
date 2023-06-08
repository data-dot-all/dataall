import { gql } from 'apollo-boost';

const updateShareRequestReason = ({ shareUri, requestPurpose }) => ({
  variables: {
    shareUri,
    requestPurpose
  },
  mutation: gql`
    mutation updateShareRequestReason(
      $shareUri: String!
      $requestPurpose: String!
    ) {
      updateShareRequestReason(shareUri: $shareUri, requestPurpose: $requestPurpose) {
        shareUri
        requestPurpose
      }
    }
  `
});

export default updateShareRequestReason;
