import { gql } from 'apollo-boost';

const linkTerm = ({ nodeUri, targetUri, targetType }) => ({
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

export default linkTerm;
