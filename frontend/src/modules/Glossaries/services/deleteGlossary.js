import { gql } from 'apollo-boost';

export const deleteGlossary = (nodeUri) => ({
  variables: {
    nodeUri
  },
  mutation: gql`
    mutation deleteGlossary($nodeUri: String!) {
      deleteGlossary(nodeUri: $nodeUri)
    }
  `
});
