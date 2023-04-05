import { gql } from 'apollo-boost';

export const requestLink = ({ nodeUri, targetUri, targetType }) => ({
  variables: {
    nodeUri,
    targetType,
    targetUri
  },
  mutation: gql`
    mutation RequestLink(
      $nodeUri: String!
      $targetUri: String!
      $targetType: String!
    ) {
      requestLink(
        nodeUri: $nodeUri
        targetUri: $targetUri
        targetType: $targetType
      ) {
        linkUri
        created
      }
    }
  `
});
