import { gql } from 'apollo-boost';

export const deleteTerm = (nodeUri) => ({
  variables: {
    nodeUri
  },
  mutation: gql`
    mutation deleteTerm($nodeUri: String!) {
      deleteTerm(nodeUri: $nodeUri)
    }
  `
});
