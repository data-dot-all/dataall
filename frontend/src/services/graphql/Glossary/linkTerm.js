import { gql } from 'apollo-boost';

export const linkTerm = ({ nodeUri, targetUri, targetType }) => ({
  variables: {
    nodeUri,
    targetType,
    targetUri
  },
  mutation: gql`
    mutation LinkTerm(
      $nodeUri: String!
      $targetUri: String!
      $targetType: String!
    ) {
      linkTerm(
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
